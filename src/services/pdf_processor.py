"""
Processador de PDFs para extração de dados de ementas e documentos acadêmicos.

Este módulo fornece funcionalidades avançadas para:
1. Extração de texto de PDFs usando múltiplas bibliotecas
2. Processamento inteligente de ementas acadêmicas
3. Identificação e estruturação de conteúdo acadêmico
4. Validação de qualidade da extração
"""
import os
import re
import tempfile
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path
from datetime import datetime
import asyncio

import pdfplumber
import fitz  # PyMuPDF
import requests
from loguru import logger

from ..models.scraped_data import SyllabusData
from ..utils.data_validator import data_validator
from ..config.settings import config


class PDFProcessor:
    """
    Classe principal para processamento de PDFs acadêmicos.
    
    Combina diferentes técnicas de extração para maximizar
    a qualidade e completude dos dados extraídos.
    """
    
    def __init__(self):
        self.logger = logger.bind(component="PDFProcessor")
        self.temp_dir = config.pdf.temp_dir
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        
        # Padrões regex para identificar seções de ementa
        self.section_patterns = {
            "objectives": [
                r"(?:objetivos?|objective|metas?|finalidade)[\s:]*(.+?)(?=\n(?:[A-Z]|$))",
                r"(?:objetivo geral|objetivo específico)[\s:]*(.+?)(?=\n(?:[A-Z]|$))"
            ],
            "syllabus_content": [
                r"(?:conteúdo programático|programa|ementa|content)[\s:]*(.+?)(?=\n(?:[A-Z]|$))",
                r"(?:unidades?|tópicos?|chapters?)[\s:]*(.+?)(?=\n(?:[A-Z]|$))"
            ],
            "methodology": [
                r"(?:metodologia|método|approach|estratégias?)[\s:]*(.+?)(?=\n(?:[A-Z]|$))",
                r"(?:recursos didáticos|material)[\s:]*(.+?)(?=\n(?:[A-Z]|$))"
            ],
            "evaluation": [
                r"(?:avaliação|evaluation|critérios?|assessment)[\s:]*(.+?)(?=\n(?:[A-Z]|$))",
                r"(?:formas? de avaliação|sistema de avaliação)[\s:]*(.+?)(?=\n(?:[A-Z]|$))"
            ],
            "bibliography": [
                r"(?:bibliografia|references?|referências?)[\s:]*(.+?)(?=\n(?:[A-Z]|$))",
                r"(?:livros? textos?|material bibliográfico)[\s:]*(.+?)(?=\n(?:[A-Z]|$))"
            ]
        }
    
    async def process_pdf_from_url(self, 
                                  pdf_url: str, 
                                  course_code: str = "", 
                                  course_name: str = "") -> Optional[SyllabusData]:
        """
        Processa um PDF a partir de uma URL.
        
        Args:
            pdf_url: URL do PDF
            course_code: Código da disciplina
            course_name: Nome da disciplina
            
        Returns:
            Dados extraídos da ementa ou None se falhou
        """
        self.logger.info(f"Processando PDF: {pdf_url}")
        
        try:
            # Download do PDF
            pdf_path = await self._download_pdf(pdf_url)
            if not pdf_path:
                return None
            
            # Processar arquivo local
            result = await self.process_pdf_file(pdf_path, course_code, course_name)
            
            # Adicionar URL original
            if result:
                result.pdf_url = pdf_url
            
            # Limpar arquivo temporário
            try:
                os.unlink(pdf_path)
            except Exception:
                pass
            
            return result
            
        except Exception as e:
            self.logger.error(f"Erro ao processar PDF da URL {pdf_url}: {e}")
            return None
    
    async def process_pdf_file(self, 
                              file_path: str, 
                              course_code: str = "", 
                              course_name: str = "") -> Optional[SyllabusData]:
        """
        Processa um arquivo PDF local.
        
        Args:
            file_path: Caminho para o arquivo PDF
            course_code: Código da disciplina
            course_name: Nome da disciplina
            
        Returns:
            Dados extraídos da ementa ou None se falhou
        """
        self.logger.info(f"Processando arquivo PDF: {file_path}")
        
        try:
            # Verificar se arquivo existe e tem tamanho válido
            if not self._validate_pdf_file(file_path):
                return None
            
            # Tentar extração com pdfplumber primeiro
            extracted_data = await self._extract_with_pdfplumber(file_path)
            
            # Se falhou, tentar com PyMuPDF
            if not extracted_data or extracted_data.get("extraction_confidence", 0) < 0.5:
                self.logger.info("Tentando extração com PyMuPDF...")
                pymupdf_data = await self._extract_with_pymupdf(file_path)
                
                if pymupdf_data and pymupdf_data.get("extraction_confidence", 0) > extracted_data.get("extraction_confidence", 0):
                    extracted_data = pymupdf_data
            
            if not extracted_data:
                self.logger.warning(f"Falha na extração de dados do PDF: {file_path}")
                return None
            
            # Enriquecer dados se código/nome foram fornecidos
            if course_code:
                extracted_data["course_code"] = course_code
            if course_name:
                extracted_data["course_name"] = course_name
            
            # Inferir informações se não foram fornecidas
            if not extracted_data.get("course_code") or not extracted_data.get("course_name"):
                inferred = self._infer_course_info(extracted_data.get("full_text", ""))
                extracted_data.update(inferred)
            
            # Validar dados mínimos
            if not extracted_data.get("course_code") and not extracted_data.get("course_name"):
                self.logger.warning("Não foi possível identificar curso no PDF")
                return None
            
            # Criar objeto SyllabusData
            syllabus_data = SyllabusData(
                course_code=extracted_data.get("course_code", ""),
                course_name=extracted_data.get("course_name", ""),
                objectives=extracted_data.get("objectives"),
                syllabus_content=extracted_data.get("syllabus_content"),
                methodology=extracted_data.get("methodology"),
                evaluation_criteria=extracted_data.get("evaluation_criteria"),
                bibliography=extracted_data.get("bibliography", []),
                competencies=extracted_data.get("competencies", []),
                pdf_url=extracted_data.get("pdf_url", f"file://{file_path}"),
                extraction_confidence=extracted_data.get("extraction_confidence", 0.0),
                source_url=extracted_data.get("pdf_url", f"file://{file_path}")
            )
            
            self.logger.info(f"PDF processado com sucesso. Confiança: {syllabus_data.extraction_confidence:.2f}")
            return syllabus_data
            
        except Exception as e:
            self.logger.error(f"Erro ao processar arquivo PDF {file_path}: {e}")
            return None
    
    async def _download_pdf(self, url: str) -> Optional[str]:
        """
        Faz download de um PDF da URL para arquivo temporário.
        
        Args:
            url: URL do PDF
            
        Returns:
            Caminho do arquivo temporário ou None se falhou
        """
        try:
            headers = {
                "User-Agent": config.browser.user_agent,
                "Accept": "application/pdf,application/octet-stream,*/*"
            }
            
            response = requests.get(url, headers=headers, stream=True, timeout=60)
            response.raise_for_status()
            
            # Verificar se é realmente um PDF
            content_type = response.headers.get('content-type', '').lower()
            if 'pdf' not in content_type and not url.lower().endswith('.pdf'):
                self.logger.warning(f"URL pode não ser um PDF: {url}")
            
            # Criar arquivo temporário
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf', dir=self.temp_dir) as temp_file:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        temp_file.write(chunk)
                
                temp_path = temp_file.name
            
            # Verificar tamanho do arquivo
            file_size = os.path.getsize(temp_path)
            max_size = config.pdf.max_file_size_mb * 1024 * 1024
            
            if file_size > max_size:
                os.unlink(temp_path)
                self.logger.error(f"PDF muito grande ({file_size / 1024 / 1024:.1f}MB): {url}")
                return None
            
            self.logger.debug(f"PDF baixado: {temp_path} ({file_size / 1024:.1f}KB)")
            return temp_path
            
        except Exception as e:
            self.logger.error(f"Erro ao baixar PDF {url}: {e}")
            return None
    
    def _validate_pdf_file(self, file_path: str) -> bool:
        """
        Valida se o arquivo é um PDF válido.
        
        Args:
            file_path: Caminho do arquivo
            
        Returns:
            True se válido
        """
        try:
            path = Path(file_path)
            
            if not path.exists():
                self.logger.error(f"Arquivo não encontrado: {file_path}")
                return False
            
            if path.stat().st_size == 0:
                self.logger.error(f"Arquivo vazio: {file_path}")
                return False
            
            # Verificar assinatura do PDF
            with open(file_path, 'rb') as f:
                header = f.read(4)
                if header != b'%PDF':
                    self.logger.error(f"Arquivo não é um PDF válido: {file_path}")
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao validar PDF {file_path}: {e}")
            return False
    
    async def _extract_with_pdfplumber(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Extrai dados usando pdfplumber.
        
        Args:
            file_path: Caminho do arquivo PDF
            
        Returns:
            Dicionário com dados extraídos
        """
        try:
            with pdfplumber.open(file_path) as pdf:
                full_text = ""
                
                # Extrair texto de todas as páginas
                for page in pdf.pages:
                    try:
                        page_text = page.extract_text()
                        if page_text:
                            full_text += page_text + "\n"
                    except Exception as e:
                        self.logger.warning(f"Erro ao extrair página: {e}")
                        continue
                
                if not full_text.strip():
                    return None
                
                # Processar texto extraído
                return self._process_extracted_text(full_text, "pdfplumber")
                
        except Exception as e:
            self.logger.error(f"Erro no pdfplumber: {e}")
            return None
    
    async def _extract_with_pymupdf(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Extrai dados usando PyMuPDF (fitz).
        
        Args:
            file_path: Caminho do arquivo PDF
            
        Returns:
            Dicionário com dados extraídos
        """
        try:
            doc = fitz.open(file_path)
            full_text = ""
            
            # Extrair texto de todas as páginas
            for page_num in range(len(doc)):
                try:
                    page = doc.load_page(page_num)
                    page_text = page.get_text()
                    if page_text:
                        full_text += page_text + "\n"
                except Exception as e:
                    self.logger.warning(f"Erro ao extrair página {page_num}: {e}")
                    continue
            
            doc.close()
            
            if not full_text.strip():
                return None
            
            # Processar texto extraído
            return self._process_extracted_text(full_text, "pymupdf")
            
        except Exception as e:
            self.logger.error(f"Erro no PyMuPDF: {e}")
            return None
    
    def _process_extracted_text(self, text: str, extractor: str) -> Dict[str, Any]:
        """
        Processa texto extraído e identifica seções.
        
        Args:
            text: Texto extraído do PDF
            extractor: Nome do extrator usado
            
        Returns:
            Dicionário com dados estruturados
        """
        # Limpar e normalizar texto
        cleaned_text = self._clean_text(text)
        
        # Extrair seções específicas
        sections = {}
        for section_name, patterns in self.section_patterns.items():
            section_content = self._extract_section(cleaned_text, patterns)
            if section_content:
                if section_name == "bibliography":
                    sections[section_name] = self._parse_bibliography(section_content)
                else:
                    sections[section_name] = section_content
        
        # Extrair competências/habilidades
        competencies = self._extract_competencies(cleaned_text)
        if competencies:
            sections["competencies"] = competencies
        
        # Calcular confiança da extração
        confidence = self._calculate_extraction_confidence(cleaned_text, sections, extractor)
        
        return {
            "full_text": cleaned_text,
            "extraction_confidence": confidence,
            **sections
        }
    
    def _clean_text(self, text: str) -> str:
        """
        Limpa e normaliza texto extraído.
        
        Args:
            text: Texto bruto
            
        Returns:
            Texto limpo
        """
        if not text:
            return ""
        
        # Remover caracteres de controle
        cleaned = re.sub(r'[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F]', '', text)
        
        # Normalizar espaços
        cleaned = re.sub(r'\s+', ' ', cleaned)
        
        # Normalizar quebras de linha
        cleaned = re.sub(r'\n\s*\n', '\n\n', cleaned)
        
        # Remover espaços no início e fim
        cleaned = cleaned.strip()
        
        return cleaned
    
    def _extract_section(self, text: str, patterns: List[str]) -> Optional[str]:
        """
        Extrai seção específica usando padrões regex.
        
        Args:
            text: Texto completo
            patterns: Lista de padrões regex
            
        Returns:
            Conteúdo da seção ou None
        """
        for pattern in patterns:
            try:
                match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
                if match:
                    content = match.group(1).strip()
                    if len(content) > 10:  # Conteúdo mínimo
                        return content
            except Exception as e:
                self.logger.warning(f"Erro no padrão regex {pattern}: {e}")
                continue
        
        return None
    
    def _parse_bibliography(self, bib_text: str) -> List[str]:
        """
        Parse bibliografia em lista de referências.
        
        Args:
            bib_text: Texto da bibliografia
            
        Returns:
            Lista de referências
        """
        if not bib_text:
            return []
        
        # Dividir por quebras de linha ou numeração
        references = []
        
        # Tentar dividir por números (1., 2., etc.)
        numbered_refs = re.split(r'\n\s*\d+\.\s*', bib_text)
        if len(numbered_refs) > 1:
            references = [ref.strip() for ref in numbered_refs[1:] if ref.strip()]
        else:
            # Tentar dividir por quebras de linha duplas
            line_refs = bib_text.split('\n\n')
            if len(line_refs) > 1:
                references = [ref.strip() for ref in line_refs if ref.strip()]
            else:
                # Fallback: dividir por quebras de linha simples
                references = [ref.strip() for ref in bib_text.split('\n') if len(ref.strip()) > 20]
        
        return references[:20]  # Limitar a 20 referências
    
    def _extract_competencies(self, text: str) -> List[str]:
        """
        Extrai competências/habilidades do texto.
        
        Args:
            text: Texto completo
            
        Returns:
            Lista de competências
        """
        competency_patterns = [
            r"(?:competências?|habilidades?|skills?)[\s:]*(.+?)(?=\n(?:[A-Z]|$))",
            r"(?:ao final|após.*curso|student.*able)[\s:]*(.+?)(?=\n(?:[A-Z]|$))",
        ]
        
        competencies = []
        
        for pattern in competency_patterns:
            try:
                matches = re.finditer(pattern, text, re.IGNORECASE | re.DOTALL)
                for match in matches:
                    comp_text = match.group(1).strip()
                    
                    # Dividir em competências individuais
                    individual_comps = re.split(r'[;\n]\s*[-•]?\s*', comp_text)
                    for comp in individual_comps:
                        comp = comp.strip()
                        if len(comp) > 15 and len(comp) < 200:
                            competencies.append(comp)
                            
            except Exception as e:
                continue
        
        return competencies[:10]  # Limitar a 10 competências
    
    def _infer_course_info(self, text: str) -> Dict[str, str]:
        """
        Tenta inferir código e nome do curso do texto.
        
        Args:
            text: Texto completo
            
        Returns:
            Dicionário com course_code e course_name
        """
        info = {}
        
        # Procurar por código de curso
        code_patterns = [
            r"(?:código|code|disciplina)[\s:]*([A-Z]{2,4}\d{3,4}[A-Z]?)",
            r"\b([A-Z]{2,4}\d{3,4}[A-Z]?)\b",
        ]
        
        for pattern in code_patterns:
            match = re.search(pattern, text[:500], re.IGNORECASE)  # Procurar no início
            if match:
                info["course_code"] = match.group(1).upper()
                break
        
        # Procurar por nome do curso (geralmente no título)
        name_patterns = [
            r"(?:disciplina|course|subject)[\s:]*([A-ZÁÀÂÃÉÊÍÓÔÕÚÇ][a-záàâãéêíóôõúç\s]+)",
            r"^([A-ZÁÀÂÃÉÊÍÓÔÕÚÇ][A-Za-záàâãéêíóôõúç\s]{10,100})",  # Primeira linha longa
        ]
        
        for pattern in name_patterns:
            match = re.search(pattern, text[:200], re.MULTILINE)
            if match:
                name = match.group(1).strip()
                if len(name) > 10 and len(name) < 100:
                    info["course_name"] = name
                    break
        
        return info
    
    def _calculate_extraction_confidence(self, 
                                       text: str, 
                                       sections: Dict[str, Any], 
                                       extractor: str) -> float:
        """
        Calcula confiança da extração baseada na qualidade dos dados.
        
        Args:
            text: Texto extraído
            sections: Seções identificadas
            extractor: Nome do extrator
            
        Returns:
            Confiança de 0.0 a 1.0
        """
        confidence = 0.0
        
        # Pontuação base por ter texto
        if text and len(text) > 100:
            confidence += 0.2
        
        # Pontuação por seções encontradas
        section_weights = {
            "objectives": 0.15,
            "syllabus_content": 0.20,
            "methodology": 0.10,
            "evaluation_criteria": 0.10,
            "bibliography": 0.15,
            "competencies": 0.10
        }
        
        for section, weight in section_weights.items():
            if sections.get(section):
                confidence += weight
        
        # Penalidade por texto muito curto ou muito longo
        text_length = len(text)
        if text_length < 500:
            confidence *= 0.7
        elif text_length > 10000:
            confidence *= 0.9
        
        # Bonus por extrator mais confiável
        if extractor == "pdfplumber":
            confidence *= 1.05
        
        # Bonus por ter informações de curso
        if sections.get("course_code") and sections.get("course_name"):
            confidence += 0.1
        
        return min(1.0, confidence)
    
    async def process_multiple_pdfs(self, 
                                   pdf_urls: List[str], 
                                   max_concurrent: int = 3) -> List[SyllabusData]:
        """
        Processa múltiplos PDFs concorrentemente.
        
        Args:
            pdf_urls: Lista de URLs de PDFs
            max_concurrent: Número máximo de processamentos simultâneos
            
        Returns:
            Lista de dados extraídos
        """
        self.logger.info(f"Processando {len(pdf_urls)} PDFs...")
        
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def process_single_pdf(url: str) -> Optional[SyllabusData]:
            async with semaphore:
                return await self.process_pdf_from_url(url)
        
        # Processar PDFs concorrentemente
        tasks = [process_single_pdf(url) for url in pdf_urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filtrar resultados válidos
        valid_results = []
        for result in results:
            if isinstance(result, SyllabusData):
                valid_results.append(result)
            elif isinstance(result, Exception):
                self.logger.error(f"Erro no processamento: {result}")
        
        self.logger.info(f"Processamento concluído: {len(valid_results)} sucessos de {len(pdf_urls)} tentativas")
        return valid_results
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """
        Retorna estatísticas de processamento.
        
        Returns:
            Dicionário com estatísticas
        """
        temp_files = list(self.temp_dir.glob("*.pdf"))
        
        return {
            "temp_files_count": len(temp_files),
            "temp_dir_size_mb": sum(f.stat().st_size for f in temp_files) / (1024 * 1024),
            "max_file_size_mb": config.pdf.max_file_size_mb,
            "extraction_timeout": config.pdf.extraction_timeout
        }
    
    def cleanup_temp_files(self, max_age_hours: int = 24):
        """
        Limpa arquivos temporários antigos.
        
        Args:
            max_age_hours: Idade máxima dos arquivos em horas
        """
        try:
            cutoff_time = datetime.now().timestamp() - (max_age_hours * 3600)
            
            temp_files = list(self.temp_dir.glob("*.pdf"))
            removed_count = 0
            
            for file_path in temp_files:
                try:
                    if file_path.stat().st_mtime < cutoff_time:
                        file_path.unlink()
                        removed_count += 1
                except Exception as e:
                    self.logger.warning(f"Erro ao remover {file_path}: {e}")
            
            self.logger.info(f"Limpeza concluída: {removed_count} arquivos removidos")
            
        except Exception as e:
            self.logger.error(f"Erro na limpeza de arquivos temporários: {e}")


# Instância global do processador
pdf_processor = PDFProcessor()