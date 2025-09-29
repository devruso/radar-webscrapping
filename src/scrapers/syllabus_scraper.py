"""
Scraper especializado para coleta de ementas de disciplinas.

Este scraper combina web scraping com processamento de PDFs para
extrair dados completos de ementas acadêmicas.

Funcionalidades:
1. Busca por links de PDFs de ementas
2. Download e processamento automático de PDFs
3. Correlação com dados de disciplinas
4. Validação de qualidade da extração
"""
import asyncio
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin, urlparse
import re

from playwright.async_api import Page
from bs4 import BeautifulSoup

from .base_scraper import BaseScraper
from ..models.scraped_data import SyllabusData, ScrapingType
from ..services.pdf_processor import pdf_processor
from ..utils.browser_manager import browser_manager
from ..utils.data_validator import data_validator
from ..config.settings import config


class SyllabusScraper(BaseScraper):
    """
    Scraper especializado para coleta de ementas de disciplinas.
    
    Demonstra integração entre web scraping e processamento de documentos,
    mostrando como extrair e processar dados de diferentes fontes.
    """
    
    def __init__(self, base_url: str = None, rate_limit: float = 2.0):
        super().__init__(base_url or config.targets.syllabus_repository, rate_limit)
        self.found_pdfs = {}  # Cache de PDFs encontrados
        self.processing_stats = {
            "pdfs_found": 0,
            "pdfs_processed": 0,
            "pdfs_failed": 0,
            "extraction_time": 0
        }
        
    @property
    def scraper_name(self) -> str:
        return "SyllabusScraper"
    
    @property
    def scraping_type(self) -> ScrapingType:
        return ScrapingType.SYLLABI
    
    def validate_config(self, config_data: Dict[str, Any]) -> bool:
        """
        Valida configuração específica para ementas.
        
        Args:
            config_data: Configuração a ser validada
            
        Returns:
            True se configuração é válida
        """
        if not config_data:
            return True
        
        # Verificar configurações específicas de PDF
        pdf_config = config_data.get("pdf_config", {})
        max_size = pdf_config.get("max_file_size_mb")
        if max_size and (max_size < 1 or max_size > 100):
            self.logger.error(f"Tamanho máximo de PDF inválido: {max_size}MB")
            return False
        
        return True
    
    async def scrape(self, config_data: Dict[str, Any] = None) -> List[SyllabusData]:
        """
        Método principal de scraping de ementas.
        
        Args:
            config_data: Configurações específicas
            
        Returns:
            Lista de ementas processadas
        """
        self.logger.info("Iniciando coleta de ementas de disciplinas")
        
        scraping_config = config_data or config.get_scraper_config("syllabi")
        target_url = scraping_config.get("target_url", self.base_url)
        
        syllabi = []
        
        try:
            # Inicializar navegador
            if not browser_manager.browser:
                await browser_manager.start()
            
            # Etapa 1: Encontrar links de PDFs
            pdf_links = await self._find_pdf_links(target_url, scraping_config)
            self.processing_stats["pdfs_found"] = len(pdf_links)
            
            if not pdf_links:
                self.logger.warning("Nenhum PDF de ementa encontrado")
                return syllabi
            
            self.logger.info(f"Encontrados {len(pdf_links)} PDFs de ementas")
            
            # Etapa 2: Processar PDFs concorrentemente
            max_concurrent = scraping_config.get("max_concurrent_pdfs", 3)
            syllabi = await self._process_pdf_batch(pdf_links, max_concurrent)
            
            # Etapa 3: Validar e enriquecer dados
            validated_syllabi = await self._validate_and_enrich_syllabi(syllabi)
            
            self.processing_stats["pdfs_processed"] = len(validated_syllabi)
            self.processing_stats["pdfs_failed"] = len(pdf_links) - len(validated_syllabi)
            
            self.logger.info(f"Processamento concluído: {len(validated_syllabi)} ementas válidas")
            return validated_syllabi
            
        except Exception as e:
            self.logger.error(f"Erro durante scraping de ementas: {e}")
            raise
    
    async def _find_pdf_links(self, target_url: str, config_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Encontra links de PDFs de ementas na página.
        
        Args:
            target_url: URL da página de ementas
            config_data: Configurações do scraping
            
        Returns:
            Lista de dicionários com informações dos PDFs
        """
        pdf_links = []
        
        try:
            async with browser_manager.get_page() as page:
                success = await browser_manager.navigate_and_wait(page, target_url)
                if not success:
                    raise Exception(f"Falha ao navegar para {target_url}")
                
                # Aguardar carregamento de elementos dinâmicos
                await page.wait_for_timeout(3000)
                
                # Estratégia 1: Procurar links diretos para PDFs
                direct_links = await self._find_direct_pdf_links(page)
                pdf_links.extend(direct_links)
                
                # Estratégia 2: Procurar em listas de disciplinas
                if not pdf_links:
                    course_links = await self._find_course_pdf_links(page)
                    pdf_links.extend(course_links)
                
                # Estratégia 3: Procurar em tabelas
                if not pdf_links:
                    table_links = await self._find_table_pdf_links(page)
                    pdf_links.extend(table_links)
                
                # Estratégia 4: Busca genérica por elementos contendo PDFs
                if not pdf_links:
                    generic_links = await self._find_generic_pdf_links(page)
                    pdf_links.extend(generic_links)
                
        except Exception as e:
            self.logger.error(f"Erro ao buscar links de PDF: {e}")
        
        # Filtrar e limpar links
        cleaned_links = self._clean_and_filter_pdf_links(pdf_links, target_url)
        return cleaned_links
    
    async def _find_direct_pdf_links(self, page: Page) -> List[Dict[str, Any]]:
        """
        Encontra links diretos para PDFs.
        
        Args:
            page: Página do Playwright
            
        Returns:
            Lista de informações de PDFs
        """
        pdf_links = []
        
        try:
            # Procurar por links que terminam com .pdf
            links = await page.query_selector_all("a[href$='.pdf'], a[href*='.pdf']")
            
            for link in links:
                try:
                    href = await link.get_attribute("href")
                    text = await link.text_content()
                    title = await link.get_attribute("title")
                    
                    if href:
                        pdf_info = {
                            "url": href,
                            "text": (text or "").strip(),
                            "title": (title or "").strip(),
                            "course_code": "",
                            "course_name": ""
                        }
                        
                        # Tentar extrair informações do curso do texto/título
                        course_info = self._extract_course_info_from_link(pdf_info["text"], pdf_info["title"])
                        pdf_info.update(course_info)
                        
                        pdf_links.append(pdf_info)
                        
                except Exception as e:
                    self.logger.warning(f"Erro ao processar link direto: {e}")
                    continue
                    
        except Exception as e:
            self.logger.error(f"Erro na busca por links diretos: {e}")
        
        return pdf_links
    
    async def _find_course_pdf_links(self, page: Page) -> List[Dict[str, Any]]:
        """
        Encontra PDFs em listas de disciplinas.
        
        Args:
            page: Página do Playwright
            
        Returns:
            Lista de informações de PDFs
        """
        pdf_links = []
        
        try:
            # Procurar por itens de curso que contenham links PDF
            course_items = await page.query_selector_all(
                ".course-item, .discipline-item, .subject-item, li, tr"
            )
            
            for item in course_items:
                try:
                    # Procurar link PDF dentro do item
                    pdf_link = await item.query_selector("a[href*='.pdf'], a[href*='ementa']")
                    if not pdf_link:
                        continue
                    
                    href = await pdf_link.get_attribute("href")
                    if not href:
                        continue
                    
                    # Extrair informações do curso do contexto
                    item_text = await item.text_content()
                    course_info = self._extract_course_info_from_text(item_text or "")
                    
                    pdf_info = {
                        "url": href,
                        "text": (item_text or "").strip(),
                        "title": "",
                        "course_code": course_info.get("course_code", ""),
                        "course_name": course_info.get("course_name", "")
                    }
                    
                    pdf_links.append(pdf_info)
                    
                except Exception as e:
                    self.logger.warning(f"Erro ao processar item de curso: {e}")
                    continue
                    
        except Exception as e:
            self.logger.error(f"Erro na busca por cursos: {e}")
        
        return pdf_links
    
    async def _find_table_pdf_links(self, page: Page) -> List[Dict[str, Any]]:
        """
        Encontra PDFs em tabelas de disciplinas.
        
        Args:
            page: Página do Playwright
            
        Returns:
            Lista de informações de PDFs
        """
        pdf_links = []
        
        try:
            # Procurar por tabelas
            tables = await page.query_selector_all("table")
            
            for table in tables:
                rows = await table.query_selector_all("tr")
                
                for row in rows[1:]:  # Pular cabeçalho
                    try:
                        # Procurar link PDF na linha
                        pdf_link = await row.query_selector("a[href*='.pdf'], a[href*='ementa']")
                        if not pdf_link:
                            continue
                        
                        href = await pdf_link.get_attribute("href")
                        if not href:
                            continue
                        
                        # Extrair informações das células
                        cells = await row.query_selector_all("td, th")
                        row_data = []
                        for cell in cells:
                            cell_text = await cell.text_content()
                            if cell_text:
                                row_data.append(cell_text.strip())
                        
                        # Tentar identificar código e nome do curso
                        course_code = ""
                        course_name = ""
                        
                        for cell_text in row_data:
                            if re.match(r"[A-Z]{2,4}\d{3,4}", cell_text):
                                course_code = cell_text
                            elif len(cell_text) > 10 and not course_name:
                                course_name = cell_text
                        
                        pdf_info = {
                            "url": href,
                            "text": " | ".join(row_data),
                            "title": "",
                            "course_code": course_code,
                            "course_name": course_name
                        }
                        
                        pdf_links.append(pdf_info)
                        
                    except Exception as e:
                        self.logger.warning(f"Erro ao processar linha da tabela: {e}")
                        continue
                        
        except Exception as e:
            self.logger.error(f"Erro na busca em tabelas: {e}")
        
        return pdf_links
    
    async def _find_generic_pdf_links(self, page: Page) -> List[Dict[str, Any]]:
        """
        Busca genérica por links de PDF.
        
        Args:
            page: Página do Playwright
            
        Returns:
            Lista de informações de PDFs
        """
        pdf_links = []
        
        try:
            # Procurar por qualquer link que pareça ser um PDF
            all_links = await page.query_selector_all("a")
            
            for link in all_links:
                try:
                    href = await link.get_attribute("href")
                    text = await link.text_content()
                    
                    if not href:
                        continue
                    
                    # Verificar se é um PDF baseado na URL ou texto
                    is_pdf = (
                        href.lower().endswith('.pdf') or
                        '.pdf' in href.lower() or
                        'ementa' in href.lower() or
                        'syllabus' in href.lower() or
                        (text and ('pdf' in text.lower() or 'ementa' in text.lower()))
                    )
                    
                    if is_pdf:
                        pdf_info = {
                            "url": href,
                            "text": (text or "").strip(),
                            "title": "",
                            "course_code": "",
                            "course_name": ""
                        }
                        
                        # Tentar extrair informações do contexto
                        course_info = self._extract_course_info_from_link(pdf_info["text"], "")
                        pdf_info.update(course_info)
                        
                        pdf_links.append(pdf_info)
                        
                except Exception as e:
                    continue
                    
        except Exception as e:
            self.logger.error(f"Erro na busca genérica: {e}")
        
        return pdf_links
    
    def _extract_course_info_from_link(self, link_text: str, title: str) -> Dict[str, str]:
        """
        Extrai informações de curso de texto de link.
        
        Args:
            link_text: Texto do link
            title: Título do link
            
        Returns:
            Dicionário com course_code e course_name
        """
        info = {"course_code": "", "course_name": ""}
        
        combined_text = f"{link_text} {title}".strip()
        if not combined_text:
            return info
        
        # Procurar código do curso
        code_match = re.search(r"([A-Z]{2,4}\d{3,4}[A-Z]?)", combined_text)
        if code_match:
            info["course_code"] = code_match.group(1)
        
        # Procurar nome do curso (texto mais longo)
        words = combined_text.split()
        if len(words) > 2:
            # Remover palavras muito curtas e códigos
            meaningful_words = [w for w in words if len(w) > 2 and not re.match(r"[A-Z]{2,4}\d{3,4}", w)]
            if meaningful_words:
                info["course_name"] = " ".join(meaningful_words[:10])  # Limitar tamanho
        
        return info
    
    def _extract_course_info_from_text(self, text: str) -> Dict[str, str]:
        """
        Extrai informações de curso de texto genérico.
        
        Args:
            text: Texto para análise
            
        Returns:
            Dicionário com course_code e course_name
        """
        info = {"course_code": "", "course_name": ""}
        
        if not text:
            return info
        
        # Procurar código do curso
        code_match = re.search(r"([A-Z]{2,4}\d{3,4}[A-Z]?)", text)
        if code_match:
            info["course_code"] = code_match.group(1)
        
        # Procurar nome do curso
        # Tentar encontrar a parte mais descritiva do texto
        sentences = text.split('.')
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 15 and len(sentence) < 100:
                # Remover código se presente
                clean_sentence = re.sub(r"[A-Z]{2,4}\d{3,4}[A-Z]?", "", sentence).strip()
                if clean_sentence and len(clean_sentence) > 10:
                    info["course_name"] = clean_sentence
                    break
        
        return info
    
    def _clean_and_filter_pdf_links(self, pdf_links: List[Dict[str, Any]], base_url: str) -> List[Dict[str, Any]]:
        """
        Limpa e filtra links de PDF.
        
        Args:
            pdf_links: Lista de links encontrados
            base_url: URL base para resolver links relativos
            
        Returns:
            Lista de links limpos e válidos
        """
        cleaned_links = []
        seen_urls = set()
        
        for pdf_info in pdf_links:
            try:
                url = pdf_info["url"]
                
                # Resolver URL relativa
                if not url.startswith(('http://', 'https://')):
                    url = urljoin(base_url, url)
                
                # Evitar duplicatas
                if url in seen_urls:
                    continue
                seen_urls.add(url)
                
                # Validar URL
                parsed = urlparse(url)
                if not parsed.netloc:
                    continue
                
                # Atualizar URL no dict
                pdf_info["url"] = url
                
                # Limpar textos
                pdf_info["text"] = data_validator.sanitize_string(pdf_info["text"], 200)
                pdf_info["title"] = data_validator.sanitize_string(pdf_info["title"], 100)
                pdf_info["course_name"] = data_validator.sanitize_string(pdf_info["course_name"], 100)
                
                cleaned_links.append(pdf_info)
                
            except Exception as e:
                self.logger.warning(f"Erro ao limpar link PDF: {e}")
                continue
        
        return cleaned_links
    
    async def _process_pdf_batch(self, pdf_links: List[Dict[str, Any]], max_concurrent: int) -> List[SyllabusData]:
        """
        Processa batch de PDFs concorrentemente.
        
        Args:
            pdf_links: Lista de informações de PDFs
            max_concurrent: Número máximo de processamentos simultâneos
            
        Returns:
            Lista de ementas processadas
        """
        self.logger.info(f"Processando {len(pdf_links)} PDFs com máximo de {max_concurrent} concorrentes")
        
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def process_single_pdf(pdf_info: Dict[str, Any]) -> Optional[SyllabusData]:
            async with semaphore:
                try:
                    # Delay entre requisições
                    await asyncio.sleep(self.rate_limit)
                    
                    # Processar PDF
                    result = await pdf_processor.process_pdf_from_url(
                        pdf_info["url"],
                        pdf_info["course_code"],
                        pdf_info["course_name"]
                    )
                    
                    if result:
                        # Enriquecer com informações adicionais do contexto
                        if not result.course_code and pdf_info["course_code"]:
                            result.course_code = pdf_info["course_code"]
                        if not result.course_name and pdf_info["course_name"]:
                            result.course_name = pdf_info["course_name"]
                    
                    return result
                    
                except Exception as e:
                    self.logger.error(f"Erro ao processar PDF {pdf_info['url']}: {e}")
                    return None
        
        # Processar PDFs concorrentemente
        tasks = [process_single_pdf(pdf_info) for pdf_info in pdf_links]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filtrar resultados válidos
        valid_syllabi = []
        for result in results:
            if isinstance(result, SyllabusData):
                valid_syllabi.append(result)
            elif isinstance(result, Exception):
                self.logger.error(f"Erro no processamento: {result}")
        
        return valid_syllabi
    
    async def _validate_and_enrich_syllabi(self, syllabi: List[SyllabusData]) -> List[SyllabusData]:
        """
        Valida e enriquece dados de ementas.
        
        Args:
            syllabi: Lista de ementas para validar
            
        Returns:
            Lista de ementas válidas
        """
        validated_syllabi = []
        
        for syllabus in syllabi:
            try:
                # Validar dados básicos
                if not syllabus.course_code and not syllabus.course_name:
                    self.logger.warning("Ementa sem identificação de curso ignorada")
                    continue
                
                # Verificar qualidade da extração
                if syllabus.extraction_confidence < 0.3:
                    self.logger.warning(f"Ementa com baixa confiança ignorada: {syllabus.extraction_confidence:.2f}")
                    continue
                
                # Sanitizar dados
                if syllabus.course_name:
                    syllabus.course_name = data_validator.sanitize_string(syllabus.course_name, 200)
                
                if syllabus.objectives:
                    syllabus.objectives = data_validator.sanitize_string(syllabus.objectives, 1000)
                
                if syllabus.syllabus_content:
                    syllabus.syllabus_content = data_validator.sanitize_string(syllabus.syllabus_content, 2000)
                
                validated_syllabi.append(syllabus)
                
            except Exception as e:
                self.logger.warning(f"Erro ao validar ementa: {e}")
                continue
        
        self.logger.info(f"Validação concluída: {len(validated_syllabi)} ementas válidas de {len(syllabi)}")
        return validated_syllabi
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """
        Retorna estatísticas do processamento.
        
        Returns:
            Dicionário com estatísticas
        """
        return {
            **self.processing_stats,
            "success_rate": (self.processing_stats["pdfs_processed"] / 
                           max(self.processing_stats["pdfs_found"], 1)) * 100,
            "pdf_processor_stats": pdf_processor.get_processing_stats()
        }