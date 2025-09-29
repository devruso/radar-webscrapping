"""
Scraper especializado para coleta de horários de turmas.

Este scraper coleta informações sobre horários de disciplinas,
incluindo professores, salas, turmas e horários específicos.

Funcionalidades:
1. Navegação através de sistemas de horários
2. Extração de dados de turmas e professores
3. Processamento de horários em diferentes formatos
4. Correlação com dados de disciplinas
"""
import asyncio
import re
from typing import List, Dict, Any, Optional, Tuple
from datetime import time
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from playwright.async_api import Page

from .base_scraper import BaseScraper
from ..models.scraped_data import Schedule, ScrapingType
from ..utils.browser_manager import browser_manager
from ..utils.data_validator import data_validator
from ..config.settings import config


class ScheduleScraper(BaseScraper):
    """
    Scraper especializado para coleta de horários de turmas.
    
    Demonstra técnicas avançadas de:
    - Processamento de horários complexos
    - Correlação de dados entre tabelas
    - Tratamento de diferentes formatos de cronograma
    """
    
    def __init__(self, base_url: str = None, rate_limit: float = 1.5):
        super().__init__(base_url or config.targets.schedule_system, rate_limit)
        self.semester_cache = {}  # Cache de semestres processados
        
    @property
    def scraper_name(self) -> str:
        return "ScheduleScraper"
    
    @property
    def scraping_type(self) -> ScrapingType:
        return ScrapingType.SCHEDULES
    
    def validate_config(self, config_data: Dict[str, Any]) -> bool:
        """
        Valida configuração específica para horários.
        
        Args:
            config_data: Configuração a ser validada
            
        Returns:
            True se configuração é válida
        """
        if not config_data:
            return True
        
        # Verificar se semestre está no formato correto
        semester = config_data.get("semester")
        if semester and not re.match(r"^20\d{2}/[12]$", semester):
            self.logger.error(f"Formato de semestre inválido: {semester}")
            return False
        
        return True
    
    async def scrape(self, config_data: Dict[str, Any] = None) -> List[Schedule]:
        """
        Método principal de scraping de horários.
        
        Args:
            config_data: Configurações específicas
            
        Returns:
            Lista de horários coletados
        """
        self.logger.info("Iniciando coleta de horários de turmas")
        
        scraping_config = config_data or config.get_scraper_config("schedules")
        target_url = scraping_config.get("target_url", self.base_url)
        semester = scraping_config.get("semester", self._get_current_semester())
        
        collected_schedules = []
        
        try:
            # Inicializar navegador
            if not browser_manager.browser:
                await browser_manager.start()
            
            # Coletar horários
            async with browser_manager.get_page() as page:
                success = await browser_manager.navigate_and_wait(page, target_url)
                if not success:
                    raise Exception(f"Falha ao navegar para {target_url}")
                
                # Detectar tipo de sistema de horários
                schedule_type = await self._detect_schedule_system_type(page)
                self.logger.info(f"Sistema de horários detectado: {schedule_type}")
                
                # Extrair horários baseado no tipo
                if schedule_type == "grade_table":
                    collected_schedules = await self._scrape_grade_table(page, semester)
                elif schedule_type == "course_list":
                    collected_schedules = await self._scrape_course_list(page, semester)
                elif schedule_type == "interactive_calendar":
                    collected_schedules = await self._scrape_interactive_calendar(page, semester)
                else:
                    # Fallback para método genérico
                    collected_schedules = await self._scrape_generic_schedules(page, semester)
                
                # Processar e enriquecer dados
                processed_schedules = await self._process_schedule_data(collected_schedules)
                
                # Validar dados
                validated_schedules = await self._validate_schedule_data(processed_schedules)
                
                self.logger.info(f"Coleta concluída: {len(validated_schedules)} horários válidos")
                return validated_schedules
                
        except Exception as e:
            self.logger.error(f"Erro durante scraping de horários: {e}")
            raise
    
    async def _detect_schedule_system_type(self, page: Page) -> str:
        """
        Detecta o tipo de sistema de horários da página.
        
        Args:
            page: Página do Playwright
            
        Returns:
            Tipo de sistema detectado
        """
        try:
            # Verificar por grade horária (tabela de horários tradicional)
            grade_table = await page.query_selector("table.grade-horarios, table.schedule-grid, .schedule-table")
            if grade_table:
                return "grade_table"
            
            # Verificar por lista de disciplinas com horários
            course_list = await page.query_selector(".course-list, .discipline-list, ul.courses")
            if course_list:
                return "course_list"
            
            # Verificar por calendário interativo
            calendar = await page.query_selector(".calendar, #calendar, [class*='calendar']")
            if calendar:
                return "interactive_calendar"
            
            # Verificar por tabela genérica
            tables = await page.query_selector_all("table")
            if len(tables) > 0:
                return "grade_table"
            
            return "unknown"
            
        except Exception as e:
            self.logger.warning(f"Erro na detecção do tipo de sistema: {e}")
            return "unknown"
    
    async def _scrape_grade_table(self, page: Page, semester: str) -> List[Schedule]:
        """
        Coleta horários de uma grade horária tradicional.
        
        Args:
            page: Página do Playwright
            semester: Semestre letivo
            
        Returns:
            Lista de horários extraídos
        """
        schedules = []
        
        try:
            # Encontrar a tabela principal
            table = await page.query_selector("table")
            if not table:
                return schedules
            
            # Extrair cabeçalho (dias da semana)
            headers = await table.query_selector_all("thead th, tr:first-child th, tr:first-child td")
            days_header = []
            for header in headers[1:]:  # Pular primeira coluna (horários)
                day_text = await header.text_content()
                if day_text:
                    days_header.append(day_text.strip())
            
            # Extrair linhas de dados
            rows = await table.query_selector_all("tbody tr, tr")
            
            for row_index, row in enumerate(rows[1:], 1):  # Pular cabeçalho
                cells = await row.query_selector_all("td, th")
                
                if len(cells) < 2:
                    continue
                
                # Primeira célula geralmente é o horário
                time_cell = cells[0]
                time_text = await time_cell.text_content()
                time_slot = time_text.strip() if time_text else ""
                
                # Processar células de cada dia
                for day_index, cell in enumerate(cells[1:]):
                    cell_content = await cell.text_content()
                    if not cell_content or cell_content.strip() == "":
                        continue
                    
                    # Extrair informações da célula
                    schedule_info = self._parse_schedule_cell_content(cell_content.strip())
                    if not schedule_info:
                        continue
                    
                    # Calcular dia da semana
                    day_of_week = day_index + 2  # Segunda = 2, Terça = 3, etc.
                    
                    # Criar objeto Schedule
                    schedule_data = {
                        "course_code": schedule_info.get("course_code", ""),
                        "class_code": schedule_info.get("class_code", f"T{day_index+1:02d}"),
                        "professor": schedule_info.get("professor", "Não informado"),
                        "schedule_text": f"{day_of_week}{time_slot}",
                        "classroom": schedule_info.get("classroom", ""),
                        "semester": semester,
                        "source_url": page.url,
                        "days_of_week": [day_of_week],
                        "start_time": self._parse_time_slot(time_slot)[0],
                        "end_time": self._parse_time_slot(time_slot)[1]
                    }
                    
                    schedule = Schedule(**schedule_data)
                    schedules.append(schedule)
                    
        except Exception as e:
            self.logger.error(f"Erro ao extrair grade horária: {e}")
        
        return schedules
    
    async def _scrape_course_list(self, page: Page, semester: str) -> List[Schedule]:
        """
        Coleta horários de uma lista de disciplinas.
        
        Args:
            page: Página do Playwright
            semester: Semestre letivo
            
        Returns:
            Lista de horários extraídos
        """
        schedules = []
        
        try:
            # Procurar por itens de curso/disciplina
            course_items = await page.query_selector_all(
                ".course-item, .discipline-item, .subject-item, li, tr"
            )
            
            for item in course_items:
                text_content = await item.text_content()
                if not text_content or len(text_content.strip()) < 10:
                    continue
                
                # Extrair informações do curso
                course_info = self._parse_course_schedule_text(text_content.strip())
                if not course_info:
                    continue
                
                # Criar Schedule com informações extraídas
                schedule_data = {
                    **course_info,
                    "semester": semester,
                    "source_url": page.url
                }
                
                # Processar horário se presente
                if schedule_data.get("schedule_text"):
                    days_times = self._parse_schedule_text(schedule_data["schedule_text"])
                    schedule_data.update(days_times)
                
                try:
                    schedule = Schedule(**schedule_data)
                    schedules.append(schedule)
                except Exception as e:
                    self.logger.warning(f"Erro ao criar Schedule: {e}")
                    continue
                    
        except Exception as e:
            self.logger.error(f"Erro ao extrair lista de cursos: {e}")
        
        return schedules
    
    def _parse_schedule_cell_content(self, content: str) -> Optional[Dict[str, str]]:
        """
        Extrai informações de uma célula de horário.
        
        Args:
            content: Conteúdo da célula
            
        Returns:
            Dicionário com informações extraídas
        """
        if not content or len(content.strip()) < 3:
            return None
        
        info = {}
        
        # Padrões para extração
        patterns = {
            "course_code": r"([A-Z]{2,4}\d{3,4}[A-Z]?)",
            "class_code": r"([TN]\d{2}[A-Z]?)",
            "classroom": r"(?:sala|room|s\.?)\s*([A-Z]?\d+[A-Z]?)",
            "professor": r"Prof\.?\s*([A-ZÁÀÂÃÉÊÍÓÔÕÚÇ][a-záàâãéêíóôõúç\s\.]+)"
        }
        
        for key, pattern in patterns.items():
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                info[key] = match.group(1).strip()
        
        # Se não encontrou professor, tentar extrair nome genérico
        if "professor" not in info:
            # Procurar por nomes (palavras capitalizadas)
            name_match = re.search(r"([A-ZÁÀÂÃÉÊÍÓÔÕÚÇ][a-záàâãéêíóôõúç]+(?:\s+[A-ZÁÀÂÃÉÊÍÓÔÕÚÇ][a-záàâãéêíóôõúç]+)*)", content)
            if name_match:
                info["professor"] = name_match.group(1)
        
        return info if info else None
    
    def _parse_course_schedule_text(self, text: str) -> Optional[Dict[str, str]]:
        """
        Extrai informações completas de horário de um texto.
        
        Args:
            text: Texto contendo informações do horário
            
        Returns:
            Dicionário com informações extraídas
        """
        if not text:
            return None
        
        info = {}
        
        # Padrões mais abrangentes
        patterns = {
            "course_code": r"([A-Z]{2,4}\d{3,4}[A-Z]?)",
            "class_code": r"(?:turma|class|t\.?)\s*([TN]?\d{2}[A-Z]?)",
            "professor": r"(?:prof\.?|professor|docente)[\s:]?\s*([A-ZÁÀÂÃÉÊÍÓÔÕÚÇ][a-záàâãéêíóôõúç\s\.]+)",
            "schedule_text": r"([1-7][MTN]\d{2,4}(?:[,-]?\s*[1-7][MTN]\d{2,4})*)",
            "classroom": r"(?:sala|room|s\.?)\s*([A-Z]?\d+[A-Z]?)"
        }
        
        for key, pattern in patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                info[key] = match.group(1).strip()
        
        # Preencher campos obrigatórios se ausentes
        info.setdefault("course_code", "")
        info.setdefault("class_code", "T01")
        info.setdefault("professor", "Não informado")
        info.setdefault("schedule_text", "")
        
        return info
    
    def _parse_schedule_text(self, schedule_text: str) -> Dict[str, Any]:
        """
        Processa texto de horário e extrai informações estruturadas.
        
        Args:
            schedule_text: Texto do horário (ex: "2M34", "246N12")
            
        Returns:
            Dicionário com dias da semana e horários
        """
        result = {
            "days_of_week": [],
            "start_time": None,
            "end_time": None
        }
        
        if not schedule_text:
            return result
        
        # Padrão para horários: [dias][turno][horários]
        # Ex: 2M34 = Segunda (2), Manhã (M), horários 3 e 4
        pattern = r"([1-7]+)([MTN])(\d{2,4})"
        
        matches = re.findall(pattern, schedule_text)
        
        all_days = set()
        earliest_time = None
        latest_time = None
        
        for days_str, shift, times_str in matches:
            # Extrair dias da semana
            days = [int(d) for d in days_str]
            all_days.update(days)
            
            # Converter horários
            start_time, end_time = self._convert_schedule_times(shift, times_str)
            
            if start_time and (earliest_time is None or start_time < earliest_time):
                earliest_time = start_time
            
            if end_time and (latest_time is None or end_time > latest_time):
                latest_time = end_time
        
        result["days_of_week"] = sorted(list(all_days))
        result["start_time"] = earliest_time
        result["end_time"] = latest_time
        
        return result
    
    def _convert_schedule_times(self, shift: str, times_str: str) -> Tuple[Optional[time], Optional[time]]:
        """
        Converte códigos de horário em objetos time.
        
        Args:
            shift: Turno (M/T/N)
            times_str: String com horários (ex: "34", "1234")
            
        Returns:
            Tuple (hora_inicio, hora_fim)
        """
        # Mapeamento básico de horários (pode ser customizado por universidade)
        time_mappings = {
            "M": {  # Manhã
                "1": (time(7, 0), time(7, 50)),
                "2": (time(7, 50), time(8, 40)),
                "3": (time(8, 50), time(9, 40)),
                "4": (time(9, 40), time(10, 30)),
                "5": (time(10, 40), time(11, 30)),
                "6": (time(11, 30), time(12, 20))
            },
            "T": {  # Tarde
                "1": (time(13, 0), time(13, 50)),
                "2": (time(13, 50), time(14, 40)),
                "3": (time(14, 50), time(15, 40)),
                "4": (time(15, 40), time(16, 30)),
                "5": (time(16, 40), time(17, 30)),
                "6": (time(17, 30), time(18, 20))
            },
            "N": {  # Noite
                "1": (time(18, 30), time(19, 20)),
                "2": (time(19, 20), time(20, 10)),
                "3": (time(20, 20), time(21, 10)),
                "4": (time(21, 10), time(22, 0))
            }
        }
        
        shift_mapping = time_mappings.get(shift.upper(), {})
        
        if not shift_mapping:
            return None, None
        
        # Extrair períodos individuais
        periods = [times_str[i] for i in range(len(times_str))]
        valid_periods = [p for p in periods if p in shift_mapping]
        
        if not valid_periods:
            return None, None
        
        # Primeiro período para hora de início
        start_time = shift_mapping[valid_periods[0]][0]
        
        # Último período para hora de fim
        end_time = shift_mapping[valid_periods[-1]][1]
        
        return start_time, end_time
    
    def _parse_time_slot(self, time_slot: str) -> Tuple[Optional[time], Optional[time]]:
        """
        Parse genérico de slot de tempo.
        
        Args:
            time_slot: Slot de tempo (ex: "M34", "T12")
            
        Returns:
            Tuple (hora_inicio, hora_fim)
        """
        if not time_slot:
            return None, None
        
        # Tentar extrair turno e horários
        match = re.match(r"([MTN])(\d+)", time_slot)
        if match:
            shift, times = match.groups()
            return self._convert_schedule_times(shift, times)
        
        return None, None
    
    async def _scrape_interactive_calendar(self, page: Page, semester: str) -> List[Schedule]:
        """
        Coleta horários de um calendário interativo.
        
        Args:
            page: Página do Playwright
            semester: Semestre letivo
            
        Returns:
            Lista de horários extraídos
        """
        schedules = []
        
        try:
            # Aguardar carregamento do calendário
            await page.wait_for_timeout(3000)
            
            # Procurar por eventos do calendário
            events = await page.query_selector_all(
                ".calendar-event, .event, .fc-event, [class*='event']"
            )
            
            for event in events:
                try:
                    # Extrair texto do evento
                    event_text = await event.text_content()
                    if not event_text:
                        continue
                    
                    # Tentar extrair atributos adicionais
                    title = await event.get_attribute("title")
                    data_info = await event.get_attribute("data-info")
                    
                    # Combinar informações
                    full_text = f"{event_text} {title or ''} {data_info or ''}".strip()
                    
                    # Extrair informações do evento
                    event_info = self._parse_course_schedule_text(full_text)
                    if not event_info:
                        continue
                    
                    schedule_data = {
                        **event_info,
                        "semester": semester,
                        "source_url": page.url
                    }
                    
                    # Processar horário
                    if schedule_data.get("schedule_text"):
                        days_times = self._parse_schedule_text(schedule_data["schedule_text"])
                        schedule_data.update(days_times)
                    
                    schedule = Schedule(**schedule_data)
                    schedules.append(schedule)
                    
                except Exception as e:
                    self.logger.warning(f"Erro ao processar evento do calendário: {e}")
                    continue
                    
        except Exception as e:
            self.logger.error(f"Erro ao extrair calendário interativo: {e}")
        
        return schedules
    
    async def _scrape_generic_schedules(self, page: Page, semester: str) -> List[Schedule]:
        """
        Método genérico para coleta de horários.
        
        Args:
            page: Página do Playwright
            semester: Semestre letivo
            
        Returns:
            Lista de horários extraídos
        """
        schedules = []
        
        try:
            # Procurar por qualquer elemento que contenha informações de horário
            elements = await page.query_selector_all("*")
            
            for element in elements:
                text_content = await element.text_content()
                if not text_content or len(text_content.strip()) < 15:
                    continue
                
                # Verificar se contém padrões de horário
                if not re.search(r"[1-7][MTN]\d{2,4}", text_content):
                    continue
                
                # Tentar extrair informações
                schedule_info = self._parse_course_schedule_text(text_content.strip())
                if not schedule_info:
                    continue
                
                schedule_data = {
                    **schedule_info,
                    "semester": semester,
                    "source_url": page.url
                }
                
                # Processar horário
                if schedule_data.get("schedule_text"):
                    days_times = self._parse_schedule_text(schedule_data["schedule_text"])
                    schedule_data.update(days_times)
                
                try:
                    schedule = Schedule(**schedule_data)
                    schedules.append(schedule)
                except Exception as e:
                    continue
                    
        except Exception as e:
            self.logger.error(f"Erro na extração genérica de horários: {e}")
        
        return schedules
    
    async def _process_schedule_data(self, schedules: List[Schedule]) -> List[Schedule]:
        """
        Processa e enriquece dados de horários coletados.
        
        Args:
            schedules: Lista de horários coletados
            
        Returns:
            Lista de horários processados
        """
        processed = []
        
        for schedule in schedules:
            try:
                # Processar texto de horário se não foi processado
                if schedule.schedule_text and not schedule.days_of_week:
                    days_times = self._parse_schedule_text(schedule.schedule_text)
                    
                    # Atualizar schedule com novos dados
                    schedule_dict = schedule.dict()
                    schedule_dict.update(days_times)
                    schedule = Schedule(**schedule_dict)
                
                processed.append(schedule)
                
            except Exception as e:
                self.logger.warning(f"Erro ao processar horário: {e}")
                continue
        
        return processed
    
    async def _validate_schedule_data(self, schedules: List[Schedule]) -> List[Schedule]:
        """
        Valida dados de horários coletados.
        
        Args:
            schedules: Lista de horários para validar
            
        Returns:
            Lista de horários válidos
        """
        validated = []
        validation_results = []
        
        for schedule in schedules:
            schedule_dict = schedule.dict()
            
            # Validar dados
            is_valid, errors = data_validator.validate_schedule_data(schedule_dict)
            validation_results.append((is_valid, errors))
            
            if is_valid:
                # Sanitizar strings
                schedule_dict["professor"] = data_validator.sanitize_string(schedule_dict["professor"], 100)
                schedule_dict["classroom"] = data_validator.sanitize_string(schedule_dict.get("classroom", ""), 50)
                
                validated_schedule = Schedule(**schedule_dict)
                validated.append(validated_schedule)
            else:
                self.logger.warning(f"Horário inválido: {schedule_dict.get('course_code', 'SEM_CÓDIGO')} - {errors}")
        
        # Log resumo
        summary = data_validator.get_validation_summary(validation_results)
        self.logger.info(f"Validação de horários: {summary['success_rate']:.1f}% de sucesso")
        
        return validated
    
    def _get_current_semester(self) -> str:
        """
        Determina o semestre atual baseado na data.
        
        Returns:
            String do semestre (ex: "2024/1")
        """
        from datetime import datetime
        
        now = datetime.now()
        year = now.year
        
        # Lógica simples: Jan-Jun = /1, Jul-Dez = /2
        semester = 1 if now.month <= 6 else 2
        
        return f"{year}/{semester}"