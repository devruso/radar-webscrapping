"""
Scraper especializado para coleta de dados de disciplinas/cursos.

Este scraper demonstra como implementar coleta de dados estruturada
usando tanto Playwright (para sites dinâmicos) quanto BeautifulSoup 
(para HTML estático).

Funcionalidades:
1. Navegação inteligente através de páginas de catálogo
2. Extração de dados estruturados de disciplinas
3. Tratamento de diferentes formatos de página
4. Cache inteligente para evitar re-scraping
"""
import asyncio
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin, urlparse
import json
from datetime import datetime

from bs4 import BeautifulSoup
from playwright.async_api import Page

from .base_scraper import BaseScraper
from ..models.scraped_data import Course, ScrapingType, ScrapingJob
from ..utils.browser_manager import browser_manager
from ..utils.data_validator import data_validator
from ..config.settings import config


class CourseScraper(BaseScraper):
    """
    Scraper especializado para coleta de dados de disciplinas.
    
    Este scraper serve como exemplo de implementação completa,
    mostrando padrões e técnicas essenciais para web scraping eficaz.
    """
    
    def __init__(self, base_url: str = None, rate_limit: float = 1.0):
        super().__init__(base_url or config.targets.course_catalog, rate_limit)
        self.collected_courses = {}  # Cache de cursos coletados
        self.failed_urls = []  # URLs que falharam
        
    @property
    def scraper_name(self) -> str:
        return "CourseScraper"
    
    @property
    def scraping_type(self) -> ScrapingType:
        return ScrapingType.COURSES
    
    def validate_config(self, config_data: Dict[str, Any]) -> bool:
        """
        Valida configuração específica para este scraper.
        
        Args:
            config_data: Configuração a ser validada
            
        Returns:
            True se configuração é válida
        """
        required_keys = ["target_url"]
        
        if not config_data:
            return True  # Usar configuração padrão
        
        for key in required_keys:
            if key not in config_data:
                self.logger.error(f"Configuração inválida: chave '{key}' ausente")
                return False
        
        # Validar URL
        target_url = config_data.get("target_url")
        if not target_url.startswith(('http://', 'https://')):
            self.logger.error(f"URL inválida: {target_url}")
            return False
        
        return True
    
    async def scrape(self, config_data: Dict[str, Any] = None) -> List[Course]:
        """
        Método principal de scraping de cursos.
        
        Args:
            config_data: Configurações específicas para este scraping
            
        Returns:
            Lista de cursos coletados
        """
        self.logger.info("Iniciando coleta de dados de disciplinas")
        
        # Usar configuração fornecida ou padrão
        scraping_config = config_data or config.get_scraper_config("courses")
        target_url = scraping_config.get("target_url", self.base_url)
        
        collected_courses = []
        
        try:
            # Inicializar navegador se necessário
            if not browser_manager.browser:
                await browser_manager.start()
            
            # Estratégia 1: Tentar com Playwright (sites dinâmicos)
            playwright_results = await self._scrape_with_playwright(target_url, scraping_config)
            if playwright_results:
                collected_courses.extend(playwright_results)
                self.logger.info(f"Coletados {len(playwright_results)} cursos via Playwright")
            
            # Estratégia 2: Se Playwright falhou, tentar com requests + BeautifulSoup
            if not collected_courses:
                self.logger.info("Tentando coleta com BeautifulSoup...")
                bs_results = await self._scrape_with_beautifulsoup(target_url, scraping_config)
                if bs_results:
                    collected_courses.extend(bs_results)
                    self.logger.info(f"Coletados {len(bs_results)} cursos via BeautifulSoup")
            
            # Validar dados coletados
            validated_courses = await self._validate_and_clean_data(collected_courses)
            
            self.logger.info(f"Scraping concluído: {len(validated_courses)} cursos válidos de {len(collected_courses)} coletados")
            return validated_courses
            
        except Exception as e:
            self.logger.error(f"Erro durante scraping de cursos: {e}")
            raise
    
    async def _scrape_with_playwright(self, target_url: str, config_data: Dict[str, Any]) -> List[Course]:
        """
        Coleta dados usando Playwright (para sites com JavaScript).
        
        Args:
            target_url: URL do catálogo de cursos
            config_data: Configurações do scraping
            
        Returns:
            Lista de cursos coletados
        """
        courses = []
        
        try:
            async with browser_manager.get_page() as page:
                # Navegar para a página principal
                success = await browser_manager.navigate_and_wait(page, target_url)
                if not success:
                    self.logger.error(f"Falha ao navegar para {target_url}")
                    return courses
                
                # Aguardar carregamento de elementos dinâmicos
                await page.wait_for_timeout(3000)
                
                # Tentar detectar automaticamente a estrutura da página
                page_structure = await self._analyze_page_structure(page)
                self.logger.info(f"Estrutura detectada: {page_structure}")
                
                # Extrair cursos baseado na estrutura detectada
                if page_structure["type"] == "table":
                    courses = await self._extract_courses_from_table(page, page_structure["selectors"])
                elif page_structure["type"] == "list":
                    courses = await self._extract_courses_from_list(page, page_structure["selectors"])
                elif page_structure["type"] == "cards":
                    courses = await self._extract_courses_from_cards(page, page_structure["selectors"])
                else:
                    # Fallback: tentar seletores genéricos
                    courses = await self._extract_courses_generic(page, config_data)
                
        except Exception as e:
            self.logger.error(f"Erro no scraping com Playwright: {e}")
        
        return courses
    
    async def _analyze_page_structure(self, page: Page) -> Dict[str, Any]:
        """
        Analisa automaticamente a estrutura da página para detectar
        o melhor método de extração.
        
        Args:
            page: Página do Playwright
            
        Returns:
            Informações sobre a estrutura detectada
        """
        structure = {"type": "unknown", "selectors": {}}
        
        try:
            # Verificar se há tabelas
            table_count = await page.evaluate("() => document.querySelectorAll('table').length")
            if table_count > 0:
                structure["type"] = "table"
                structure["selectors"] = {
                    "container": "table",
                    "rows": "tbody tr, tr",
                    "cells": "td, th"
                }
                return structure
            
            # Verificar se há listas estruturadas
            list_count = await page.evaluate("""() => {
                const lists = document.querySelectorAll('ul, ol');
                return Array.from(lists).filter(list => 
                    list.children.length > 5 && 
                    list.textContent.length > 200
                ).length;
            }""")
            
            if list_count > 0:
                structure["type"] = "list"
                structure["selectors"] = {
                    "container": "ul, ol",
                    "items": "li",
                    "content": "li"
                }
                return structure
            
            # Verificar se há cards ou divs estruturadas
            card_patterns = [
                ".course-card, .course-item, .discipline-card",
                "[class*='course'], [class*='discipline']",
                ".row .col, .grid-item"
            ]
            
            for pattern in card_patterns:
                count = await page.evaluate(f"() => document.querySelectorAll('{pattern}').length")
                if count > 3:
                    structure["type"] = "cards"
                    structure["selectors"] = {
                        "container": pattern,
                        "items": pattern,
                        "content": pattern
                    }
                    return structure
            
        except Exception as e:
            self.logger.warning(f"Erro na análise de estrutura: {e}")
        
        return structure
    
    async def _extract_courses_from_table(self, page: Page, selectors: Dict[str, str]) -> List[Course]:
        """
        Extrai cursos de uma estrutura de tabela.
        
        Args:
            page: Página do Playwright
            selectors: Seletores específicos da tabela
            
        Returns:
            Lista de cursos extraídos
        """
        courses = []
        
        try:
            # Obter todas as linhas da tabela
            rows = await page.query_selector_all(selectors["rows"])
            
            for row in rows:
                try:
                    # Extrair células da linha
                    cells = await row.query_selector_all("td")
                    if len(cells) < 3:  # Mínimo de colunas esperado
                        continue
                    
                    # Tentar mapear células para campos (ordem comum)
                    course_data = {}
                    
                    # Primeira célula geralmente é código
                    if len(cells) > 0:
                        code_text = await cells[0].text_content()
                        course_data["course_code"] = code_text.strip() if code_text else ""
                    
                    # Segunda célula geralmente é nome
                    if len(cells) > 1:
                        name_text = await cells[1].text_content()
                        course_data["course_name"] = name_text.strip() if name_text else ""
                    
                    # Terceira célula geralmente é créditos
                    if len(cells) > 2:
                        credits_text = await cells[2].text_content()
                        try:
                            course_data["credits"] = int(credits_text.strip()) if credits_text else 0
                        except ValueError:
                            course_data["credits"] = 0
                    
                    # Quarta célula pode ser departamento
                    if len(cells) > 3:
                        dept_text = await cells[3].text_content()
                        course_data["department"] = dept_text.strip() if dept_text else ""
                    
                    # Preencher campos obrigatórios se ausentes
                    course_data.setdefault("department", "Não informado")
                    course_data.setdefault("workload", course_data.get("credits", 0) * 15)
                    course_data["source_url"] = page.url
                    
                    # Criar objeto Course se dados mínimos estão presentes
                    if course_data.get("course_code") and course_data.get("course_name"):
                        course = Course(**course_data)
                        courses.append(course)
                        
                except Exception as e:
                    self.logger.warning(f"Erro ao processar linha da tabela: {e}")
                    continue
                    
        except Exception as e:
            self.logger.error(f"Erro ao extrair cursos da tabela: {e}")
        
        return courses
    
    async def _extract_courses_from_list(self, page: Page, selectors: Dict[str, str]) -> List[Course]:
        """
        Extrai cursos de uma estrutura de lista.
        
        Args:
            page: Página do Playwright
            selectors: Seletores específicos da lista
            
        Returns:
            Lista de cursos extraídos
        """
        courses = []
        
        try:
            # Obter todos os itens da lista
            items = await page.query_selector_all(selectors["items"])
            
            for item in items:
                try:
                    # Extrair texto completo do item
                    text_content = await item.text_content()
                    if not text_content:
                        continue
                    
                    # Tentar extrair informações usando regex
                    course_data = self._extract_course_info_from_text(text_content.strip())
                    if not course_data:
                        continue
                    
                    course_data["source_url"] = page.url
                    
                    # Criar objeto Course
                    course = Course(**course_data)
                    courses.append(course)
                    
                except Exception as e:
                    self.logger.warning(f"Erro ao processar item da lista: {e}")
                    continue
                    
        except Exception as e:
            self.logger.error(f"Erro ao extrair cursos da lista: {e}")
        
        return courses
    
    async def _extract_courses_from_cards(self, page: Page, selectors: Dict[str, str]) -> List[Course]:
        """
        Extrai cursos de uma estrutura de cards/divs.
        
        Args:
            page: Página do Playwright
            selectors: Seletores específicos dos cards
            
        Returns:
            Lista de cursos extraídos
        """
        courses = []
        
        try:
            # Obter todos os cards
            cards = await page.query_selector_all(selectors["items"])
            
            for card in cards:
                try:
                    course_data = {}
                    
                    # Tentar extrair dados usando seletores comuns
                    selectors_map = {
                        "course_code": [".code", ".course-code", "[class*='code']", "h3", "h4"],
                        "course_name": [".name", ".title", ".course-name", "h2", "h3"],
                        "credits": [".credits", ".credit", "[class*='credit']"],
                        "department": [".department", ".dept", "[class*='dept']"],
                        "description": [".description", ".desc", "p"]
                    }
                    
                    for field, possible_selectors in selectors_map.items():
                        for selector in possible_selectors:
                            try:
                                element = await card.query_selector(selector)
                                if element:
                                    text = await element.text_content()
                                    if text and text.strip():
                                        if field == "credits":
                                            try:
                                                course_data[field] = int(text.strip())
                                            except ValueError:
                                                continue
                                        else:
                                            course_data[field] = text.strip()
                                        break
                            except:
                                continue
                    
                    # Preencher campos obrigatórios se ausentes
                    course_data.setdefault("department", "Não informado")
                    course_data.setdefault("workload", course_data.get("credits", 0) * 15)
                    course_data["source_url"] = page.url
                    
                    # Criar objeto Course se dados mínimos estão presentes
                    if course_data.get("course_code") and course_data.get("course_name"):
                        course = Course(**course_data)
                        courses.append(course)
                        
                except Exception as e:
                    self.logger.warning(f"Erro ao processar card: {e}")
                    continue
                    
        except Exception as e:
            self.logger.error(f"Erro ao extrair cursos dos cards: {e}")
        
        return courses
    
    async def _extract_courses_generic(self, page: Page, config_data: Dict[str, Any]) -> List[Course]:
        """
        Método genérico de extração quando estrutura específica não é detectada.
        
        Args:
            page: Página do Playwright
            config_data: Configurações do scraping
            
        Returns:
            Lista de cursos extraídos
        """
        courses = []
        
        try:
            # Usar seletores da configuração se disponíveis
            selectors = config_data.get("selectors", {})
            
            # Seletores genéricos comuns
            generic_selectors = [
                "tr", "li", ".row", ".item", ".course", ".discipline",
                "[class*='course']", "[class*='discipline']"
            ]
            
            for selector in generic_selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    if len(elements) > 5:  # Provavelmente encontrou dados estruturados
                        for element in elements:
                            text_content = await element.text_content()
                            if text_content:
                                course_data = self._extract_course_info_from_text(text_content.strip())
                                if course_data:
                                    course_data["source_url"] = page.url
                                    course = Course(**course_data)
                                    courses.append(course)
                        
                        if courses:  # Se encontrou cursos, para por aqui
                            break
                            
                except Exception as e:
                    continue
                    
        except Exception as e:
            self.logger.error(f"Erro na extração genérica: {e}")
        
        return courses
    
    def _extract_course_info_from_text(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Extrai informações de curso de um texto usando regex.
        
        Args:
            text: Texto contendo informações do curso
            
        Returns:
            Dicionário com dados extraídos ou None
        """
        import re
        
        if len(text) < 10:  # Texto muito curto
            return None
        
        course_data = {}
        
        # Padrão para código de curso (ex: INF001, MAT123, ENG1234)
        code_pattern = r'\b([A-Z]{2,4}\d{3,4}[A-Z]?)\b'
        code_match = re.search(code_pattern, text)
        if code_match:
            course_data["course_code"] = code_match.group(1)
        
        # Padrão para créditos (ex: 4 créditos, 6 cred)
        credits_pattern = r'(\d{1,2})\s*(?:créditos?|cred|cr)'
        credits_match = re.search(credits_pattern, text, re.IGNORECASE)
        if credits_match:
            course_data["credits"] = int(credits_match.group(1))
        
        # Nome do curso (geralmente a parte mais longa)
        words = text.split()
        longest_phrase = ""
        for i in range(len(words)):
            for j in range(i+3, min(i+10, len(words)+1)):  # Frases de 3-10 palavras
                phrase = " ".join(words[i:j])
                if len(phrase) > len(longest_phrase) and not re.search(r'\d{4}|\d{3}', phrase):
                    longest_phrase = phrase
        
        if longest_phrase:
            course_data["course_name"] = longest_phrase.strip()
        
        # Verificar se temos dados mínimos
        if not course_data.get("course_code") and not course_data.get("course_name"):
            return None
        
        # Preencher campos padrão
        course_data.setdefault("department", "Não informado")
        course_data.setdefault("credits", 4)
        course_data.setdefault("workload", course_data.get("credits", 4) * 15)
        
        return course_data
    
    async def _scrape_with_beautifulsoup(self, target_url: str, config_data: Dict[str, Any]) -> List[Course]:
        """
        Coleta dados usando requests + BeautifulSoup (para HTML estático).
        
        Args:
            target_url: URL do catálogo
            config_data: Configurações do scraping
            
        Returns:
            Lista de cursos coletados
        """
        courses = []
        
        try:
            import requests
            
            # Fazer requisição HTTP
            headers = {
                "User-Agent": config.browser.user_agent,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8"
            }
            
            response = requests.get(target_url, headers=headers, timeout=30)
            response.raise_for_status()
            
            # Parse HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Tentar diferentes estratégias de extração
            courses = self._extract_with_beautifulsoup_heuristics(soup, target_url)
            
        except Exception as e:
            self.logger.error(f"Erro no scraping com BeautifulSoup: {e}")
        
        return courses
    
    def _extract_with_beautifulsoup_heuristics(self, soup: BeautifulSoup, source_url: str) -> List[Course]:
        """
        Extrai cursos usando heurísticas com BeautifulSoup.
        
        Args:
            soup: Objeto BeautifulSoup da página
            source_url: URL da página
            
        Returns:
            Lista de cursos extraídos
        """
        courses = []
        
        # Estratégia 1: Procurar por tabelas
        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            if len(rows) > 3:  # Tabela com dados
                table_courses = self._extract_from_table_bs(rows, source_url)
                courses.extend(table_courses)
        
        # Estratégia 2: Procurar por listas
        if not courses:
            lists = soup.find_all(['ul', 'ol'])
            for ul in lists:
                items = ul.find_all('li')
                if len(items) > 5:  # Lista com dados
                    list_courses = self._extract_from_list_bs(items, source_url)
                    courses.extend(list_courses)
        
        # Estratégia 3: Procurar por divs estruturadas
        if not courses:
            patterns = [
                {'class': lambda x: x and any(keyword in str(x).lower() for keyword in ['course', 'discipline', 'subject'])},
                {'class': 'row'},
                {'class': 'item'}
            ]
            
            for pattern in patterns:
                divs = soup.find_all('div', pattern)
                if len(divs) > 3:
                    div_courses = self._extract_from_divs_bs(divs, source_url)
                    courses.extend(div_courses)
                    if courses:
                        break
        
        return courses
    
    def _extract_from_table_bs(self, rows: List, source_url: str) -> List[Course]:
        """Extrai cursos de linhas de tabela com BeautifulSoup"""
        courses = []
        
        for row in rows[1:]:  # Pular cabeçalho
            cells = row.find_all(['td', 'th'])
            if len(cells) >= 2:
                try:
                    course_data = {
                        "course_code": cells[0].get_text(strip=True) if len(cells) > 0 else "",
                        "course_name": cells[1].get_text(strip=True) if len(cells) > 1 else "",
                        "credits": 4,  # Padrão
                        "department": cells[2].get_text(strip=True) if len(cells) > 2 else "Não informado",
                        "workload": 60,  # Padrão
                        "source_url": source_url
                    }
                    
                    # Tentar extrair créditos se presente
                    if len(cells) > 2:
                        credits_text = cells[2].get_text(strip=True)
                        try:
                            course_data["credits"] = int(credits_text)
                            course_data["workload"] = course_data["credits"] * 15
                        except ValueError:
                            pass
                    
                    if course_data["course_code"] and course_data["course_name"]:
                        course = Course(**course_data)
                        courses.append(course)
                        
                except Exception as e:
                    continue
        
        return courses
    
    def _extract_from_list_bs(self, items: List, source_url: str) -> List[Course]:
        """Extrai cursos de itens de lista com BeautifulSoup"""
        courses = []
        
        for item in items:
            text = item.get_text(strip=True)
            course_data = self._extract_course_info_from_text(text)
            if course_data:
                course_data["source_url"] = source_url
                try:
                    course = Course(**course_data)
                    courses.append(course)
                except Exception as e:
                    continue
        
        return courses
    
    def _extract_from_divs_bs(self, divs: List, source_url: str) -> List[Course]:
        """Extrai cursos de divs com BeautifulSoup"""
        courses = []
        
        for div in divs:
            text = div.get_text(strip=True)
            course_data = self._extract_course_info_from_text(text)
            if course_data:
                course_data["source_url"] = source_url
                try:
                    course = Course(**course_data)
                    courses.append(course)
                except Exception as e:
                    continue
        
        return courses
    
    async def _validate_and_clean_data(self, courses: List[Course]) -> List[Course]:
        """
        Valida e limpa dados coletados.
        
        Args:
            courses: Lista de cursos para validar
            
        Returns:
            Lista de cursos válidos
        """
        validated_courses = []
        validation_results = []
        
        for course in courses:
            # Converter para dict para validação
            course_dict = course.dict()
            
            # Validar dados
            is_valid, errors = data_validator.validate_course_data(course_dict)
            validation_results.append((is_valid, errors))
            
            if is_valid:
                # Sanitizar strings
                course_dict["course_name"] = data_validator.sanitize_string(course_dict["course_name"], 200)
                course_dict["department"] = data_validator.sanitize_string(course_dict["department"], 100)
                course_dict["course_code"] = course_dict["course_code"].upper().strip()
                
                # Recriar objeto com dados limpos
                clean_course = Course(**course_dict)
                validated_courses.append(clean_course)
            else:
                self.logger.warning(f"Curso inválido removido: {course_dict.get('course_code', 'SEM_CÓDIGO')} - Erros: {errors}")
        
        # Log resumo da validação
        summary = data_validator.get_validation_summary(validation_results)
        self.logger.info(f"Validação concluída: {summary['success_rate']:.1f}% de sucesso ({summary['valid_items']}/{summary['total_items']})")
        
        return validated_courses