"""
Gerenciador do navegador Playwright para web scraping.

Este módulo fornece:
1. Configuração otimizada do Playwright
2. Gerenciamento de contextos e páginas
3. Interceptação de requisições e respostas
4. Tratamento de elementos dinâmicos e SPAs
"""
import asyncio
from typing import Optional, Dict, Any, List
from contextlib import asynccontextmanager
from playwright.async_api import async_playwright, Browser, BrowserContext, Page, Playwright
from loguru import logger


class BrowserManager:
    """
    Gerenciador principal do navegador Playwright.
    
    Fornece uma interface simplificada para:
    - Inicializar navegadores com configurações otimizadas
    - Gerenciar contextos e páginas
    - Implementar estratégias anti-detecção
    - Controlar recursos e performance
    """
    
    def __init__(self, 
                 browser_type: str = "chromium",
                 headless: bool = True,
                 user_agent: Optional[str] = None,
                 viewport: Dict[str, int] = None):
        """
        Inicializa o gerenciador do navegador.
        
        Args:
            browser_type: Tipo do navegador (chromium, firefox, webkit)
            headless: Se deve rodar em modo headless
            user_agent: User agent customizado
            viewport: Configurações de viewport
        """
        self.browser_type = browser_type
        self.headless = headless
        self.user_agent = user_agent or self._get_default_user_agent()
        self.viewport = viewport or {"width": 1920, "height": 1080}
        
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.default_context: Optional[BrowserContext] = None
        
        self.logger = logger.bind(component="BrowserManager")
    
    def _get_default_user_agent(self) -> str:
        """Retorna um user agent padrão realista"""
        return ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36")
    
    async def start(self):
        """Inicia o Playwright e o navegador"""
        self.logger.info(f"Iniciando navegador {self.browser_type}")
        
        self.playwright = await async_playwright().start()
        
        # Configurações do navegador
        browser_args = []
        if not self.headless:
            browser_args.extend([
                "--disable-blink-features=AutomationControlled",
                "--disable-extensions"
            ])
        
        # Iniciar navegador específico
        if self.browser_type == "chromium":
            self.browser = await self.playwright.chromium.launch(
                headless=self.headless,
                args=browser_args
            )
        elif self.browser_type == "firefox":
            self.browser = await self.playwright.firefox.launch(headless=self.headless)
        elif self.browser_type == "webkit":
            self.browser = await self.playwright.webkit.launch(headless=self.headless)
        else:
            raise ValueError(f"Tipo de navegador não suportado: {self.browser_type}")
        
        # Criar contexto padrão
        self.default_context = await self._create_stealth_context()
        
        self.logger.info("Navegador iniciado com sucesso")
    
    async def _create_stealth_context(self) -> BrowserContext:
        """
        Cria um contexto do navegador com configurações anti-detecção.
        
        Returns:
            Contexto configurado
        """
        context = await self.browser.new_context(
            user_agent=self.user_agent,
            viewport=self.viewport,
            locale="pt-BR",
            timezone_id="America/Sao_Paulo",
            # Configurações anti-detecção
            java_script_enabled=True,
            accept_downloads=False,
            ignore_https_errors=True,
            # Headers customizados
            extra_http_headers={
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
                "Accept-Encoding": "gzip, deflate, br",
                "DNT": "1",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
            }
        )
        
        # Injetar scripts anti-detecção
        await context.add_init_script("""
            // Remove webdriver property
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });
            
            // Override plugins length
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5],
            });
            
            // Override languages
            Object.defineProperty(navigator, 'languages', {
                get: () => ['pt-BR', 'pt', 'en-US', 'en'],
            });
            
            // Mock chrome runtime
            window.chrome = {
                runtime: {},
            };
            
            // Override permissions
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );
        """)
        
        return context
    
    @asynccontextmanager
    async def get_page(self, context: Optional[BrowserContext] = None):
        """
        Context manager para obter uma página.
        
        Args:
            context: Contexto específico (usa o padrão se None)
            
        Yields:
            Página configurada
        """
        ctx = context or self.default_context
        page = await ctx.new_page()
        
        try:
            # Configurar interceptadores
            await self._setup_page_interceptors(page)
            yield page
        finally:
            await page.close()
    
    async def _setup_page_interceptors(self, page: Page):
        """
        Configura interceptadores para a página.
        
        Args:
            page: Página a ser configurada
        """
        # Bloquear recursos desnecessários para performance
        await page.route("**/*", self._handle_route)
        
        # Log de erros de console
        page.on("console", self._handle_console_message)
        page.on("pageerror", self._handle_page_error)
    
    async def _handle_route(self, route):
        """
        Manipula rotas para otimizar performance.
        
        Args:
            route: Rota interceptada
        """
        # Bloquear recursos desnecessários
        resource_type = route.request.resource_type
        
        if resource_type in ["image", "media", "font", "stylesheet"]:
            # Bloquear imagens, mídia, fontes e CSS para performance
            await route.abort()
        else:
            await route.continue_()
    
    def _handle_console_message(self, msg):
        """Manipula mensagens do console do navegador"""
        if msg.type == "error":
            self.logger.warning(f"Console error: {msg.text}")
    
    def _handle_page_error(self, error):
        """Manipula erros de página"""
        self.logger.error(f"Page error: {error}")
    
    async def navigate_and_wait(self, 
                               page: Page, 
                               url: str, 
                               wait_for: str = "networkidle",
                               timeout: int = 30000) -> bool:
        """
        Navega para uma URL e aguarda carregamento completo.
        
        Args:
            page: Página a ser usada
            url: URL de destino
            wait_for: Condição de espera (load, domcontentloaded, networkidle)
            timeout: Timeout em ms
            
        Returns:
            True se navegação foi bem-sucedida
        """
        try:
            self.logger.info(f"Navegando para: {url}")
            
            response = await page.goto(url, wait_until=wait_for, timeout=timeout)
            
            if response and response.status >= 400:
                self.logger.warning(f"Resposta HTTP {response.status} para {url}")
                return False
            
            # Aguardar um pouco mais para JavaScript terminar
            await page.wait_for_timeout(2000)
            
            self.logger.debug(f"Navegação completada: {url}")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro na navegação para {url}: {e}")
            return False
    
    async def wait_for_element(self, 
                              page: Page, 
                              selector: str, 
                              timeout: int = 10000,
                              state: str = "visible") -> bool:
        """
        Aguarda um elemento aparecer na página.
        
        Args:
            page: Página a ser verificada
            selector: Seletor CSS do elemento
            timeout: Timeout em ms
            state: Estado esperado (visible, attached, detached, hidden)
            
        Returns:
            True se elemento foi encontrado
        """
        try:
            await page.wait_for_selector(selector, timeout=timeout, state=state)
            return True
        except Exception as e:
            self.logger.warning(f"Elemento não encontrado {selector}: {e}")
            return False
    
    async def extract_text_from_elements(self, 
                                        page: Page, 
                                        selector: str) -> List[str]:
        """
        Extrai texto de todos os elementos que correspondem ao seletor.
        
        Args:
            page: Página a ser analisada
            selector: Seletor CSS
            
        Returns:
            Lista de textos extraídos
        """
        try:
            elements = await page.query_selector_all(selector)
            texts = []
            
            for element in elements:
                text = await element.text_content()
                if text and text.strip():
                    texts.append(text.strip())
            
            return texts
            
        except Exception as e:
            self.logger.error(f"Erro ao extrair texto de {selector}: {e}")
            return []
    
    async def take_screenshot(self, 
                             page: Page, 
                             path: str, 
                             full_page: bool = True) -> bool:
        """
        Tira screenshot da página.
        
        Args:
            page: Página para screenshot
            path: Caminho do arquivo
            full_page: Se deve capturar página inteira
            
        Returns:
            True se screenshot foi salvo
        """
        try:
            await page.screenshot(path=path, full_page=full_page)
            self.logger.info(f"Screenshot salvo: {path}")
            return True
        except Exception as e:
            self.logger.error(f"Erro ao salvar screenshot: {e}")
            return False
    
    async def stop(self):
        """Para o navegador e libera recursos"""
        self.logger.info("Parando navegador")
        
        if self.default_context:
            await self.default_context.close()
        
        if self.browser:
            await self.browser.close()
        
        if self.playwright:
            await self.playwright.stop()
        
        self.logger.info("Navegador parado")


# Instância global para uso compartilhado
browser_manager = BrowserManager()