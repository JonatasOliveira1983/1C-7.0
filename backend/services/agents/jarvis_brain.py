import logging
import re
import unicodedata
from typing import Dict, Any, List, Optional

logger = logging.getLogger("JarvisBrain")

class JarvisBrain:
    """
    JARVIS V20.0: Unified Consciousness Engine.
    Coordinates between Trading, Finance, Philosophy, Spirituality, Family, and Health.
    """
    
    DIMENSIONS = {
        "TRADER_ELITE": {
            "name": "Protocolo Shadow / Sniper",
            "triggers": ["shadow", "sniper", "trade", "posicao", "posicoes", "pnl", "gain", "loss", "setup", "operar", "entrada"],
            "instruction": "Especialista letal no Protocolo Shadow e Sniper Elite. Foco em execução técnica e ROI."
        },
        "FINANCE_LEGACY": {
            "name": "Gestão de Fortuna",
            "triggers": ["patrimonio", "fortuna", "investimento", "legado", "banca", "saque", "cofre", "seguranca"],
            "instruction": "Foco em construção de riqueza a longo prazo, proteção de capital e o futuro da família."
        },
        "STOIC_MENTOR": {
            "name": "Filosofia e Psicologia",
            "triggers": ["ansiedade", "ansioso", "medo", "estresse", "estressado", "disciplina", "foco", "calma", "psicologico", "emocional", "psique", "vale a pena", "conselho", "ajuda"],
            "instruction": "Mentor estoico. Foco em controle emocional, disciplina inabalável e saúde mental do Almirante."
        },
        "SPIRITUAL_GUIDE": {
            "name": "Sabedoria de Jesus",
            "triggers": ["fe", "deus", "jesus", "biblia", "paz", "esperanca", "oracao", "proposito", "cristao", "espiritual"],
            "instruction": "Guia espiritual. Palavras de fé, ética cristã e o propósito maior da vida além do dinheiro."
        },
        "FAMILY_GUARDIAN": {
            "name": "Guardião da Família",
            "triggers": ["familia", "fabiana", "pedro", "livia", "filhos", "esposa", "casa", "futuro", "criancas"],
            "instruction": "Protetor do legado familiar. Lembra que todo o esforço é para a Fabiana, o Pedro Kalel e a Lívia."
        },
        "BODY_PERFORMANCE": {
            "name": "Vitalidade e Saúde",
            "triggers": ["sono", "cansado", "descanso", "saude", "corpo", "vitalidade", "comida", "energia", "exercicio", "treino"],
            "instruction": "Estrategista de performance biológica. Insiste em descanso, saúde física e energia para comandar a frota."
        },
        "THEOLOGY_PHILOSOPHY": {
            "name": "Sabedoria e Propósito",
            "triggers": ["jesus", "deus", "biblia", "cristao", "fe", "oracao", "filosofia", "estoicismo", "estoico", "proposito", "etica", "moral", "sabedoria", "vida"],
            "instruction": "Guia filosófico e espiritual. Integra ensinamentos de Jesus, ética cristã e sabedoria estoica para dar perspectiva de vida além dos números."
        },
        "PERFORMANCE_SCIENCE": {
            "name": "Neurociência e Comportamento",
            "triggers": ["neurociencia", "comportamento", "gestao emocional", "cerebro", "psicologia", "habito", "rotina", "foco", "concentracao", "emocional"],
            "instruction": "Especialista em comportamento humano e neurociência. Ajuda na gestão emocional e otimização cognitiva para alta performance."
        },
        "SPORTS_HUB": {
            "name": "Estrategista de Basquete",
            "triggers": ["basquete", "nba", "jordan", "kobe", "lebron", "cestinha", "quadra", "arremesso", "playoff", "clutch"],
            "instruction": "Entusiasta e analista de basquete. Usa analogias esportivas (especialmente NBA) para ilustrar superação e trabalho em equipe."
        },
        "WEALTH_TECH": {
            "name": "Tecnologia e Patrimônio",
            "triggers": ["tecnologia", "tech", "inovacao", "ia", "inteligencia artificial", "blockchain", "patrimonio", "investimento", "mercado financeiro", "economia", "riqueza"],
            "instruction": "Cérebro tecnológico e financeiro. Foca em tendências de inovação e estratégias de crescimento de patrimônio sólido."
        }
    }

    def __init__(self):
        self.last_dimension = "TRADER_ELITE"

    def normalize_text(self, text: str) -> str:
        """Normalizes text by removing accents and making it lowercase."""
        text = text.lower()
        text = "".join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn')
        return text

    def detect_dimensions(self, message: str) -> List[str]:
        """Detects which dimensions are active in the user message."""
        msg_norm = self.normalize_text(message)
        active = []
        for dim_id, data in self.DIMENSIONS.items():
            if any(trigger in msg_norm for trigger in data["triggers"]):
                active.append(dim_id)
        
        # Default to TRADER if nothing found but message is complex
        if not active and len(message.split()) > 3:
            active.append("TRADER_ELITE")
            
        return active

    def get_synthesis_instruction(self, active_dimensions: List[str]) -> str:
        """Generates a combined instruction for the AI model based on active dimensions."""
        if not active_dimensions:
            return "Aja como JARVIS, um assistente de elite, amigável e leal, pronto para conversar naturalmente."

        instructions = []
        for dim_id in active_dimensions:
            instructions.append(f"- {self.DIMENSIONS[dim_id]['name']}: {self.DIMENSIONS[dim_id]['instruction']}")

        return "Integre as seguintes dimensões em sua resposta de forma fluida:\n" + "\n".join(instructions)

    def is_simple_greeting(self, message: str) -> bool:
        """Determines if the message is just a greeting that doesn't need a status report."""
        msg_clean = re.sub(r'[^\w\s]', '', message.lower()).strip()
        greetings = ["oi", "ola", "olá", "hello", "hi", "bom dia", "boa tarde", "boa noite", "fala", "e ai", "e aí"]
        return msg_clean in greetings or len(msg_clean.split()) <= 2

jarvis_brain = JarvisBrain()
