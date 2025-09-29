"""
Implementação concreta do scraper de cursos do SIGAA UFBA.

Implementa as interfaces de scraping de cursos usando Selenium
para coleta de dados do sistema SIGAA da UFBA.
"""

from typing import List, Optional, Dict, Any
import asyncio
import time
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from ...application.interfaces.IScrapingService import ICursoScrapingService
from ...domain.entities import Curso
from ...domain.value_objects import CodigoCurso, NomeCurso
from ...domain.exceptions import ScrapingException, ValidationException
from ...shared.logging import get_logger

logger = get_logger(__name__)


class SigaaUfbaCursoScraper(ICursoScrapingService):
    """
    Scraper concreto para coleta de cursos do SIGAA UFBA.
    
    Implementa a interface ICursoScrapingService para coleta
    de dados de cursos usando Selenium WebDriver.
    """
    
    # URLs do SIGAA UFBA
    BASE_URL = "https://sigaa.ufba.br"
    CURSOS_URL = f"{BASE_URL}/sigaa/public/curso/busca_curso_form.jsf"
    
    def __init__(self, 
                 headless: bool = True,
                 timeout: int = 30,
                 delay_between_requests: float = 1.0):
        """
        Inicializa o scraper.
        
        Args:
            headless: Se deve executar browser em modo headless
            timeout: Timeout para operações em segundos
            delay_between_requests: Delay entre requisições em segundos
        """
        self._headless = headless
        self._timeout = timeout
        self._delay = delay_between_requests
        self._driver: Optional[webdriver.Chrome] = None
        self._wait: Optional[WebDriverWait] = None
    
    async def scrape_cursos(self,
                           filtro_unidade: Optional[str] = None,
                           filtro_modalidade: Optional[str] = None) -> List[Curso]:
        """
        Coleta lista de cursos do SIGAA UFBA.
        
        Args:
            filtro_unidade: Filtrar por unidade específica
            filtro_modalidade: Filtrar por modalidade específica
            
        Returns:
            Lista de cursos coletados
            
        Raises:
            ScrapingException: Em caso de erro na coleta
        """
        try:
            logger.info("Iniciando scraping de cursos do SIGAA UFBA")
            
            # Configurar driver
            await self._inicializar_driver()
            
            # Navegar para página de busca
            await self._navegar_para_busca_cursos()
            
            # Aplicar filtros se fornecidos
            if filtro_unidade or filtro_modalidade:
                await self._aplicar_filtros(filtro_unidade, filtro_modalidade)
            
            # Coletar dados dos cursos
            cursos = await self._coletar_cursos_da_pagina()
            
            logger.info(f"Coletados {len(cursos)} cursos do SIGAA UFBA")
            return cursos
            
        except Exception as e:
            logger.error(f"Erro no scraping de cursos: {e}")
            raise ScrapingException("scraping_cursos_sigaa", str(e))
        
        finally:
            await self._finalizar_driver()
    
    async def obter_detalhes_curso(self, codigo_curso: str) -> Optional[Curso]:
        """
        Obtém detalhes específicos de um curso.
        
        Args:
            codigo_curso: Código do curso a ser coletado
            
        Returns:
            Curso com detalhes ou None se não encontrado
        """
        try:
            logger.info(f"Obtendo detalhes do curso {codigo_curso}")
            
            await self._inicializar_driver()
            
            # Buscar curso específico
            curso = await self._buscar_curso_especifico(codigo_curso)
            
            if curso:
                # Coletar detalhes adicionais
                await self._coletar_detalhes_adicionais(curso)
            
            return curso
            
        except Exception as e:
            logger.error(f"Erro ao obter detalhes do curso {codigo_curso}: {e}")
            raise ScrapingException(f"detalhes_curso_{codigo_curso}", str(e))
        
        finally:
            await self._finalizar_driver()
    
    async def validar_configuracao(self, configuracao: Dict[str, Any]) -> bool:
        """
        Valida se a configuração é válida para este scraper.
        
        Args:
            configuracao: Dicionário com configurações
            
        Returns:
            True se configuração é válida
        """
        try:
            # Validações básicas
            if not isinstance(configuracao, dict):
                return False
            
            # Testar conectividade com SIGAA
            return await self._testar_conectividade()
            
        except Exception as e:
            logger.error(f"Erro na validação de configuração: {e}")
            return False
    
    async def _inicializar_driver(self) -> None:
        """Inicializa o WebDriver Chrome."""
        try:
            options = Options()
            
            if self._headless:
                options.add_argument('--headless')
            
            # Configurações para melhor performance
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            options.add_argument('--window-size=1920,1080')
            
            # User agent
            options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
            
            self._driver = webdriver.Chrome(options=options)
            self._wait = WebDriverWait(self._driver, self._timeout)
            
            logger.debug("WebDriver inicializado com sucesso")
            
        except Exception as e:
            logger.error(f"Erro ao inicializar WebDriver: {e}")
            raise ScrapingException("inicializar_driver", str(e))
    
    async def _finalizar_driver(self) -> None:
        """Finaliza o WebDriver."""
        try:
            if self._driver:
                self._driver.quit()
                self._driver = None
                self._wait = None
                logger.debug("WebDriver finalizado")
                
        except Exception as e:
            logger.warning(f"Erro ao finalizar WebDriver: {e}")
    
    async def _navegar_para_busca_cursos(self) -> None:
        """Navega para a página de busca de cursos."""
        try:
            logger.debug(f"Navegando para {self.CURSOS_URL}")
            self._driver.get(self.CURSOS_URL)
            
            # Aguardar carregamento da página
            await self._aguardar_elemento_presente(By.TAG_NAME, "form")
            
            await asyncio.sleep(self._delay)
            
        except TimeoutException:
            raise ScrapingException("navegacao_busca", "Timeout ao carregar página de busca")
    
    async def _aplicar_filtros(self, 
                             filtro_unidade: Optional[str],
                             filtro_modalidade: Optional[str]) -> None:
        """Aplica filtros na busca de cursos."""
        try:
            logger.debug(f"Aplicando filtros - Unidade: {filtro_unidade}, Modalidade: {filtro_modalidade}")
            
            # Implementar lógica de filtros específica do SIGAA
            # Por exemplo, selecionar dropdown de unidade/modalidade
            
            if filtro_unidade:
                await self._selecionar_unidade(filtro_unidade)
            
            if filtro_modalidade:
                await self._selecionar_modalidade(filtro_modalidade)
            
            # Clicar no botão de busca
            await self._executar_busca()
            
        except Exception as e:
            logger.error(f"Erro ao aplicar filtros: {e}")
            raise ScrapingException("aplicar_filtros", str(e))
    
    async def _coletar_cursos_da_pagina(self) -> List[Curso]:
        """Coleta dados dos cursos da página atual."""
        try:
            cursos = []
            
            # Aguardar resultados da busca
            await self._aguardar_elemento_presente(By.CLASS_NAME, "resultado-busca", timeout=10)
            
            # Encontrar elementos de cursos
            elementos_cursos = self._driver.find_elements(By.CSS_SELECTOR, "[data-curso]")
            
            logger.debug(f"Encontrados {len(elementos_cursos)} elementos de curso")
            
            for elemento in elementos_cursos:
                try:
                    curso = await self._extrair_dados_curso(elemento)
                    if curso:
                        cursos.append(curso)
                        
                except Exception as e:
                    logger.warning(f"Erro ao extrair curso individual: {e}")
                    continue
                
                # Delay entre extrações
                await asyncio.sleep(self._delay * 0.1)
            
            return cursos
            
        except TimeoutException:
            logger.warning("Timeout aguardando resultados - retornando lista vazia")
            return []
        
        except Exception as e:
            logger.error(f"Erro ao coletar cursos da página: {e}")
            raise ScrapingException("coletar_cursos_pagina", str(e))
    
    async def _extrair_dados_curso(self, elemento) -> Optional[Curso]:
        """Extrai dados de um elemento de curso."""
        try:
            # Extrair dados básicos do elemento
            codigo_texto = elemento.find_element(By.CLASS_NAME, "codigo-curso").text.strip()
            nome_texto = elemento.find_element(By.CLASS_NAME, "nome-curso").text.strip()
            unidade_texto = elemento.find_element(By.CLASS_NAME, "unidade-curso").text.strip()
            
            # Dados opcionais
            municipio = self._extrair_texto_seguro(elemento, By.CLASS_NAME, "municipio-curso")
            modalidade = self._extrair_texto_seguro(elemento, By.CLASS_NAME, "modalidade-curso")
            turno = self._extrair_texto_seguro(elemento, By.CLASS_NAME, "turno-curso")
            grau = self._extrair_texto_seguro(elemento, By.CLASS_NAME, "grau-curso")
            
            # URL do curso (se disponível)
            url_elemento = elemento.find_element(By.TAG_NAME, "a")
            url_origem = url_elemento.get_attribute("href") if url_elemento else self.CURSOS_URL
            
            # Criar entidade Curso
            curso = Curso(
                codigo=CodigoCurso(codigo_texto),
                nome=NomeCurso(nome_texto),
                unidade_vinculacao=unidade_texto,
                municipio_funcionamento=municipio or "Salvador",  # Default
                modalidade=modalidade or "Presencial",  # Default
                turno=turno or "Integral",  # Default
                grau_academico=grau or "Bacharelado",  # Default
                url_origem=url_origem
            )
            
            logger.debug(f"Curso extraído: {curso.codigo} - {curso.nome}")
            return curso
            
        except NoSuchElementException as e:
            logger.warning(f"Elemento não encontrado ao extrair curso: {e}")
            return None
        
        except Exception as e:
            logger.error(f"Erro ao extrair dados do curso: {e}")
            return None
    
    def _extrair_texto_seguro(self, elemento, by: By, selector: str) -> Optional[str]:
        """Extrai texto de elemento de forma segura."""
        try:
            sub_elemento = elemento.find_element(by, selector)
            return sub_elemento.text.strip() if sub_elemento else None
        except NoSuchElementException:
            return None
    
    async def _aguardar_elemento_presente(self, 
                                        by: By, 
                                        selector: str, 
                                        timeout: Optional[int] = None) -> None:
        """Aguarda elemento estar presente na página."""
        timeout_usado = timeout or self._timeout
        self._wait.until(EC.presence_of_element_located((by, selector)))
    
    async def _buscar_curso_especifico(self, codigo_curso: str) -> Optional[Curso]:
        """Busca um curso específico pelo código."""
        try:
            # Navegar para busca
            await self._navegar_para_busca_cursos()
            
            # Preencher campo de busca com código
            campo_busca = self._wait.until(
                EC.presence_of_element_located((By.ID, "campo-codigo-curso"))
            )
            campo_busca.clear()
            campo_busca.send_keys(codigo_curso)
            
            # Executar busca
            await self._executar_busca()
            
            # Coletar resultados
            cursos = await self._coletar_cursos_da_pagina()
            
            # Retornar primeiro curso encontrado (deve ser único)
            return cursos[0] if cursos else None
            
        except Exception as e:
            logger.error(f"Erro na busca específica de curso {codigo_curso}: {e}")
            return None
    
    async def _coletar_detalhes_adicionais(self, curso: Curso) -> None:
        """Coleta detalhes adicionais do curso."""
        try:
            # Navegar para página de detalhes do curso
            if curso.url_origem and curso.url_origem != self.CURSOS_URL:
                self._driver.get(curso.url_origem)
                await asyncio.sleep(self._delay)
                
                # Coletar informações adicionais da página de detalhes
                # (implementar conforme estrutura do SIGAA)
                logger.debug(f"Detalhes adicionais coletados para {curso.codigo}")
                
        except Exception as e:
            logger.warning(f"Erro ao coletar detalhes adicionais: {e}")
    
    async def _selecionar_unidade(self, unidade: str) -> None:
        """Seleciona unidade no filtro."""
        # Implementar seleção específica do SIGAA
        pass
    
    async def _selecionar_modalidade(self, modalidade: str) -> None:
        """Seleciona modalidade no filtro."""
        # Implementar seleção específica do SIGAA
        pass
    
    async def _executar_busca(self) -> None:
        """Executa a busca clicando no botão."""
        try:
            botao_busca = self._wait.until(
                EC.element_to_be_clickable((By.ID, "botao-buscar"))
            )
            botao_busca.click()
            await asyncio.sleep(self._delay)
            
        except TimeoutException:
            raise ScrapingException("executar_busca", "Botão de busca não encontrado")
    
    async def _testar_conectividade(self) -> bool:
        """Testa conectividade com o SIGAA."""
        try:
            await self._inicializar_driver()
            self._driver.get(self.BASE_URL)
            
            # Verificar se página carregou corretamente
            self._wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            
            return True
            
        except Exception as e:
            logger.error(f"Falha no teste de conectividade: {e}")
            return False
        
        finally:
            await self._finalizar_driver()