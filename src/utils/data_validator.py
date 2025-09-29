"""
Utilitários para validação de dados coletados pelo web scraping.

Este módulo fornece:
1. Validação de integridade dos dados
2. Sanitização de strings
3. Verificação de formatos específicos (códigos de curso, horários, etc.)
4. Detecção de anomalias nos dados coletados
"""
import re
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, time
from loguru import logger


class DataValidator:
    """
    Classe principal para validação de dados coletados.
    
    Fornece métodos específicos para validar diferentes tipos de dados
    acadêmicos e garantir a qualidade das informações antes do envio
    para a API backend.
    """
    
    def __init__(self):
        self.logger = logger.bind(component="DataValidator")
        
        # Padrões regex para validação
        self.patterns = {
            "course_code": re.compile(r"^[A-Z]{2,4}\d{3,4}[A-Z]?$"),
            "class_code": re.compile(r"^[TN]\d{2}[A-Z]?$"),
            "email": re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"),
            "time_slot": re.compile(r"^[1-7][MTN]\d{2,4}$"),
            "semester": re.compile(r"^20\d{2}/[12]$"),
            "professor_name": re.compile(r"^[A-ZÁÀÂÃÉÊÍÓÔÕÚÇ][a-záàâãéêíóôõúç\s\.]+$")
        }
    
    def validate_course_data(self, course_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Valida dados de uma disciplina.
        
        Args:
            course_data: Dicionário com dados da disciplina
            
        Returns:
            Tuple (is_valid, error_messages)
        """
        errors = []
        
        # Validações obrigatórias
        required_fields = ["course_code", "course_name", "credits", "department"]
        for field in required_fields:
            if not course_data.get(field):
                errors.append(f"Campo obrigatório ausente: {field}")
        
        # Validar código da disciplina
        course_code = course_data.get("course_code", "")
        if course_code and not self.patterns["course_code"].match(course_code):
            errors.append(f"Código de disciplina inválido: {course_code}")
        
        # Validar nome da disciplina
        course_name = course_data.get("course_name", "")
        if course_name:
            if len(course_name) < 3:
                errors.append("Nome da disciplina muito curto")
            elif len(course_name) > 200:
                errors.append("Nome da disciplina muito longo")
            
            # Verificar se não é apenas números
            if course_name.isdigit():
                errors.append("Nome da disciplina não pode ser apenas números")
        
        # Validar créditos
        credits = course_data.get("credits")
        if credits is not None:
            try:
                credits_int = int(credits)
                if credits_int < 1 or credits_int > 20:
                    errors.append(f"Número de créditos inválido: {credits}")
            except (ValueError, TypeError):
                errors.append(f"Créditos deve ser um número: {credits}")
        
        # Validar carga horária
        workload = course_data.get("workload")
        if workload is not None:
            try:
                workload_int = int(workload)
                if workload_int < 15 or workload_int > 300:
                    errors.append(f"Carga horária inválida: {workload}")
            except (ValueError, TypeError):
                errors.append(f"Carga horária deve ser um número: {workload}")
        
        # Validar departamento
        department = course_data.get("department", "")
        if department and len(department) < 2:
            errors.append("Nome do departamento muito curto")
        
        return len(errors) == 0, errors
    
    def validate_schedule_data(self, schedule_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Valida dados de horário de turma.
        
        Args:
            schedule_data: Dicionário com dados do horário
            
        Returns:
            Tuple (is_valid, error_messages)
        """
        errors = []
        
        # Validações obrigatórias
        required_fields = ["course_code", "class_code", "professor", "schedule_text", "semester"]
        for field in required_fields:
            if not schedule_data.get(field):
                errors.append(f"Campo obrigatório ausente: {field}")
        
        # Validar código da turma
        class_code = schedule_data.get("class_code", "")
        if class_code and not self.patterns["class_code"].match(class_code):
            errors.append(f"Código de turma inválido: {class_code}")
        
        # Validar horário
        schedule_text = schedule_data.get("schedule_text", "")
        if schedule_text:
            if not self.validate_schedule_format(schedule_text):
                errors.append(f"Formato de horário inválido: {schedule_text}")
        
        # Validar professor
        professor = schedule_data.get("professor", "")
        if professor:
            if len(professor) < 3:
                errors.append("Nome do professor muito curto")
            elif not self.patterns["professor_name"].match(professor):
                errors.append(f"Nome de professor inválido: {professor}")
        
        # Validar semestre
        semester = schedule_data.get("semester", "")
        if semester and not self.patterns["semester"].match(semester):
            errors.append(f"Formato de semestre inválido: {semester}")
        
        # Validar números de alunos
        max_students = schedule_data.get("max_students")
        enrolled_students = schedule_data.get("enrolled_students")
        
        if max_students is not None:
            try:
                max_int = int(max_students)
                if max_int < 1 or max_int > 500:
                    errors.append(f"Número máximo de alunos inválido: {max_students}")
            except (ValueError, TypeError):
                errors.append(f"Número máximo de alunos deve ser um número: {max_students}")
        
        if enrolled_students is not None:
            try:
                enrolled_int = int(enrolled_students)
                if enrolled_int < 0:
                    errors.append(f"Número de alunos matriculados não pode ser negativo: {enrolled_students}")
                elif max_students and enrolled_int > int(max_students):
                    errors.append("Alunos matriculados não pode exceder máximo")
            except (ValueError, TypeError):
                errors.append(f"Número de alunos matriculados deve ser um número: {enrolled_students}")
        
        return len(errors) == 0, errors
    
    def validate_professor_data(self, professor_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Valida dados de professor.
        
        Args:
            professor_data: Dicionário com dados do professor
            
        Returns:
            Tuple (is_valid, error_messages)
        """
        errors = []
        
        # Validações obrigatórias
        required_fields = ["name", "department"]
        for field in required_fields:
            if not professor_data.get(field):
                errors.append(f"Campo obrigatório ausente: {field}")
        
        # Validar nome
        name = professor_data.get("name", "")
        if name:
            if len(name) < 3:
                errors.append("Nome do professor muito curto")
            elif not self.patterns["professor_name"].match(name):
                errors.append(f"Nome de professor inválido: {name}")
        
        # Validar email
        email = professor_data.get("email", "")
        if email and not self.patterns["email"].match(email):
            errors.append(f"Email inválido: {email}")
        
        # Validar URL do Lattes
        lattes_url = professor_data.get("lattes_url", "")
        if lattes_url and not lattes_url.startswith("http://lattes.cnpq.br/"):
            errors.append(f"URL do Lattes inválida: {lattes_url}")
        
        return len(errors) == 0, errors
    
    def validate_schedule_format(self, schedule_text: str) -> bool:
        """
        Valida formato de horário (ex: 2M34, 4T56, 246N12).
        
        Args:
            schedule_text: Texto do horário
            
        Returns:
            True se formato é válido
        """
        if not schedule_text:
            return False
        
        # Remover espaços e dividir por vírgulas se houver múltiplos horários
        schedules = [s.strip() for s in schedule_text.replace(" ", "").split(",")]
        
        for schedule in schedules:
            if not self.patterns["time_slot"].match(schedule):
                return False
        
        return True
    
    def sanitize_string(self, text: str, max_length: Optional[int] = None) -> str:
        """
        Sanitiza uma string removendo caracteres indesejados.
        
        Args:
            text: Texto a ser sanitizado
            max_length: Comprimento máximo (trunca se exceder)
            
        Returns:
            Texto sanitizado
        """
        if not text:
            return ""
        
        # Remover caracteres de controle e espaços extras
        sanitized = re.sub(r'\s+', ' ', str(text).strip())
        
        # Remover caracteres não imprimíveis
        sanitized = ''.join(char for char in sanitized if char.isprintable())
        
        # Truncar se necessário
        if max_length and len(sanitized) > max_length:
            sanitized = sanitized[:max_length].strip()
        
        return sanitized
    
    def detect_encoding_issues(self, text: str) -> List[str]:
        """
        Detecta possíveis problemas de encoding em texto.
        
        Args:
            text: Texto a ser analisado
            
        Returns:
            Lista de problemas encontrados
        """
        issues = []
        
        if not text:
            return issues
        
        # Verificar caracteres de replacement
        if '\ufffd' in text:
            issues.append("Caracteres de replacement (encoding incorreto)")
        
        # Verificar sequências suspeitas
        suspicious_patterns = [
            r'Ã[¡-¿]',  # Caracteres com acentos mal codificados
            r'â€™',      # Aspas simples mal codificadas
            r'â€œ|â€',   # Aspas duplas mal codificadas
        ]
        
        for pattern in suspicious_patterns:
            if re.search(pattern, text):
                issues.append(f"Possível problema de encoding: {pattern}")
        
        return issues
    
    def validate_data_consistency(self, data_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analisa consistência em uma lista de dados.
        
        Args:
            data_list: Lista de dicionários de dados
            
        Returns:
            Relatório de consistência
        """
        if not data_list:
            return {"status": "empty", "message": "Lista vazia"}
        
        report = {
            "total_items": len(data_list),
            "duplicates": 0,
            "missing_fields": {},
            "inconsistent_formats": {},
            "outliers": []
        }
        
        seen_items = set()
        field_formats = {}
        
        for i, item in enumerate(data_list):
            # Detectar duplicatas (baseado em campos-chave)
            key_fields = ["course_code", "class_code", "name"]
            item_key = tuple(item.get(field, "") for field in key_fields if field in item)
            
            if item_key in seen_items:
                report["duplicates"] += 1
            else:
                seen_items.add(item_key)
            
            # Analisar campos ausentes
            for field, value in item.items():
                if not value:
                    if field not in report["missing_fields"]:
                        report["missing_fields"][field] = 0
                    report["missing_fields"][field] += 1
                else:
                    # Analisar formatos inconsistentes
                    if field not in field_formats:
                        field_formats[field] = {"formats": set(), "lengths": []}
                    
                    field_formats[field]["formats"].add(type(value).__name__)
                    field_formats[field]["lengths"].append(len(str(value)))
        
        # Identificar formatos inconsistentes
        for field, info in field_formats.items():
            if len(info["formats"]) > 1:
                report["inconsistent_formats"][field] = list(info["formats"])
            
            # Identificar outliers de comprimento
            lengths = info["lengths"]
            if lengths:
                avg_length = sum(lengths) / len(lengths)
                for i, length in enumerate(lengths):
                    if length > avg_length * 3:  # 3x maior que a média
                        report["outliers"].append({
                            "item_index": i,
                            "field": field,
                            "length": length,
                            "avg_length": avg_length
                        })
        
        return report
    
    def get_validation_summary(self, validation_results: List[Tuple[bool, List[str]]]) -> Dict[str, Any]:
        """
        Gera resumo de resultados de validação.
        
        Args:
            validation_results: Lista de resultados (is_valid, errors)
            
        Returns:
            Resumo da validação
        """
        total = len(validation_results)
        valid = sum(1 for result in validation_results if result[0])
        invalid = total - valid
        
        all_errors = []
        for _, errors in validation_results:
            all_errors.extend(errors)
        
        # Contar tipos de erro
        error_counts = {}
        for error in all_errors:
            error_type = error.split(":")[0]  # Primeira parte antes dos dois pontos
            error_counts[error_type] = error_counts.get(error_type, 0) + 1
        
        return {
            "total_items": total,
            "valid_items": valid,
            "invalid_items": invalid,
            "success_rate": (valid / total * 100) if total > 0 else 0,
            "total_errors": len(all_errors),
            "error_types": error_counts,
            "most_common_errors": sorted(error_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        }


# Instância global do validador
data_validator = DataValidator()