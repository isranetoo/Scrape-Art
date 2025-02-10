
import re
from typing import Literal


POLO_TIPOS: dict[str, set[str]] = {
    "ATIVO/PASSIVO": {
        "APTE/APDO", "APDO/APTE", "APTE/APDA", "APDA/APTE",
        "EMBGTE/EMBGDO", "EMBGTE/EMBGDA", "EMBGDO/EMBGTE", "EMBGDA/EMBGTE",
        "RECTE/RECDO", "RCRDO/RCRTE", "RCRDA/RCRTE",
    },
    "ATIVO": {
        "REQTE", "AUTOR", "AUTORA", "EMBARGTE", "IMPUGTE", "REPRTATEAT", "EMBARGDA", "RECLAMANTE", "LIQDTEAT",
        "IMPUGDO",  "HERDEIRO", "HERDEIRA", "INVTANTE", "RECONVINTE", "EXEQTE", "IMPTTE", "ALIMENTADO",
        "RECORRENTE", "EXQTE", "REQUERENTE", "REMETENTE", "DEPRECANTE", "APELANTE", "AGRAVTE",
        "EXEQUENTE", "EXEQÜENTE", "EMBARGANTE", "EMBTE", "AGRAVANTE", "AGRAVANT", "POLO ATIVO", "ATIVA",
        "INVENTARIANTE", "IMPUGNANTE", "SUSCITANTE", "CONFTE", "PROMOVENTE", "DEMANDANTE", "DEPRECAN", "OPOENTE",
        "CONSIGNANTE", "MPF", "MINISTÉRIO PÚBLICO", "MP", "ORDENANTE", "RECORREN", "REQUISITANTE"

        # Processos Criminais
        "VÍTIMA", "PACIENTE",
    },
    "PASSIVO": {
        "RÉU", "RÉU/RÉ", "RÉ", "REU", "RÉU ESPÓLIO DE", "REQDA", "REQDO", "REQUERIDO", "REQUERIDA",
        "AGRAVDO", "AGRAVADA", "AGRAVADO", "AGRAVDA", "EXCDO", "EXECTDA", "EXECUTADO", "EXECUTADA", "EXECTDO", "EXEQUIDO", "EXEQUIDA",
        "RECORRIDO", "RECORRIDA", "IMPETRADO", "DEPRECADO", "IMPUGNADO", "RECONVINDO", "RECLAMADO", "RECLAMADA", "SUCEDIDO",
        "IMPTDO", "LIQDTEPA", "EMBARGADO", "EMBARGADA", "EMBDO", "EMBARGDO", "INTIMADO",  "POLO PASSIVO", "ORDENADO",
        "APELADO", "APELADA", "SUSCITADO", "PROMOVIDO", "DEMANDADO", "DEPRECAD", "OPOSTO" "CONSIGNADO", "RECORRID"

        # Processos Criminais
        "INDICIADO", "INVESTIGADO",
    },
    "REP":  {
        "ADV", "ADVOGADA", "ADVOGADO", "SOC ADVOGADO", "SOCIEDADE DE ADVOGADO",
        "REPRELEG", "REPRESENTANTE", "REPRESENTANTE LEGAL", "REPRTATE", "REPR POR"
        "PROC/S/OAB", "PROCURADOR",

        # Processos Criminais
        "IMPETRANTE",
    },
    "OUTROS": {
        "OUTROS PARTICIPANTE", "NÃO IDENTIFICADO", "NÃO INFORMADO", "OUTRO",
        "GUARDIÃO", "ENVOLVIDO", "INTIMADA", "TESTEMUNHA", "AUTOR DO FATO",
        "INTERESSADO", "INTERESSADA", "INTERESDO", "INTERESDA", "INTERE", "INTSSADO",
        "OUTROS INTERESSADO", "TERCEIRO INTERESSADO", "TERCEIRO", "TERINTCER", "CREDOR", "CREDOR SUPER",
        "PERITO", "FISCAL DA LEI", "MAGISTRADO", "MAGISTRADO UPJ",
        "JUIZ", "JUIZ ATUAL", "JUIZ REMETENTE", "JUÍZO RECORRENTE", "JUIZO RECORRENTE", "JUÍZO DEPRECANTE",
        "DESEMBARGADOR RELATOR", "RELATOR", "RELATORA", "RELATOR CONVOCADO", "DESEMBARGADOR",
        "ADMTERC", "FILIAÇÃO", "ADMINISTRADOR JUDICIAL", "CUSTOS LEGI", "ASSISTENTE", "AUTORIDADE",
        "ARREMTERC", "ESPÓLIO", "GESTOR", "SÍNDICO", "ADMINISTRADOR", "MASSA FALIDA",
        "LITISPA", "LITISCONSORTE", "ASSISTP", "UNIDADE EXTERNA", "MEDIADOR"
    }
}

POLOS: set[str] = {"ATIVO/PASSIVO", "ATIVO", "PASSIVO", "OUTROS", "REP", "REP_ATIVO/PASSIVO", "REP_ATIVO", "REP_PASSIVO"}
TIPOS: set[str] = set().union(*POLO_TIPOS.values())


def list_to_str(lconv: list[str]) -> str:
    """ Converte uma lista para um string

    Args:
        lconv: lista a ser convertida

    Returns:
        Lista convertida em string separada por virugulas
    """
    return str(lconv).replace("'", "").replace('"', '')


def parse_cnj(cnj: str) -> tuple[str, str, str, str, str, str]:
    """ Coleta informações importantes do numero cnj do processo

    Args:
        cnj: numero cnj do processno

    Returns:
        area_code, tribunal_code, vara_code, ano, area, tribunal
    """
    area_map = {
        "1": "STF", "2": "CNJ", "3": "STJ", "4": "Federal",
        "5": "Trabalhista", "6": "Eleitoral", "8": "Civil",
        "7": "Militar Federal", "9": "Militar Estadual"
    }

    eleit_trib_map = {
        "1": "TRE-AC", "2": "TRE-AL", "3": "TRE-AP", "4": "TRE-AM", "5": "TRE-BA",
        "6": "TRE-CE", "7": "TRE-DF", "8": "TRE-ES", "9": "TRE-GO", "10": "TRE-MA",
        "11": "TRE-MT", "12": "TRE-MS", "13": "TRE-MG", "14": "TRE-PA",
        "15": "TRE-PB", "16": "TRE-PR", "17": "TRE-PE", "18": "TRE-PI",
        "19": "TRE-RJ", "20": "TRE-RN", "21": "TRE-RS", "22": "TRE-RO",
        "23": "TRE-RR", "24": "TRE-SC", "25": "TRE-SE", "26": "TRE-SP", "27": "TRE-TO"
    }

    civil_trib_map = {
        "1": "TJAC", "2": "TJAL", "3": "TJAP", "4": "TJAM", "5": "TJBA",
        "6": "TJCE", "7": "TJDF", "8": "TJES", "9": "TJGO", "10": "TJMA",
        "11": "TJMT", "12": "TJMS", "13": "TJMG", "14": "TJPA",
        "15": "TJPB", "16": "TJPR", "17": "TJPE", "18": "TJPI",
        "19": "TJRJ", "20": "TJRN", "21": "TJRS", "22": "TJRO",
        "23": "TJRR", "24": "TJSC", "25": "TJSE", "26": "TJSP", "27": "TJTO"
    }

    mil_fed_map = {
        "1": "TJMMG", "2": "TJMRS", "3": "TJMSP"
    }

    ano = cnj.split(".")[-4]
    area_code = cnj.split(".")[-3]
    tribunal_code = cnj.split(".")[-2].lstrip('0')
    vara_code = cnj.split(".")[-1]

    if area_code == "1":
        tribunal = "STF"
    elif area_code == "2":
        tribunal = "CNJ"
    elif area_code == "3":
        tribunal = "STJ"
    elif area_code == "4":
        tribunal = "TRF" + tribunal_code
    elif area_code == "5":
       tribunal = "TST" if len(tribunal_code) == 0 else "TRT-" + tribunal_code
    elif area_code == "6":
        tribunal = eleit_trib_map.get(tribunal_code, "UKN")
    elif area_code == "7":
        tribunal = "CJM" + tribunal_code
    elif area_code == "8":
        tribunal = civil_trib_map.get(tribunal_code, "UKN")
    elif area_code == "9":
        tribunal = mil_fed_map.get(tribunal_code, "UKN")

    return area_code, tribunal_code, vara_code, ano, area_map[area_code], tribunal


def parse_cnpj(cnpj: str) -> tuple[str, str]:
    """ Parseia cnpj para formato padrão

    Args:
        cnpj: cnpj desformatado

    Returns:
        cnpj formatado, raiz do cnpj formatada
    """
    cnpj = re.sub(" ", "", cnpj)

    pattern_cnpj = r"(\d\d)\.?(\d\d\d)\.?(\d\d\d)\/?(\d\d\d\d)\-?(\d\d)"
    mc = re.match(pattern_cnpj, cnpj)
    pcnpj = None if mc is None else f"{mc.group(1)}.{mc.group(2)}.{mc.group(3)}/{mc.group(4)}-{mc.group(5)}"

    pattern_raiz = r"(\d\d)\.?(\d\d\d)\.?(\d\d\d)"
    mr = re.match(pattern_raiz, cnpj)
    raiz = None if mr is None else f"{mr.group(1)}.{mr.group(2)}.{mr.group(3)}"

    return pcnpj, raiz


def parse_valor(valor: str, mil_sep: str = ".", dec_sep: str = ",") -> float:
    """ Converte um valor financeiro que esta em string para float

    Args:
        valor: valor a ser convertido em float

    Returns:
        valor convertido em float
    """
    if isinstance(valor, str):
        return float(valor.replace(" ", "").replace(mil_sep, "").replace(dec_sep, ".").replace("R$", ""))
    return valor


def parse_phone(telefone: str) -> str:
    """ Parseia telefone para formato padrão

    Args:
        telefone: telefone desformatado

    Returns:
        telefone formatado
    """
    telefone = re.sub(" ", "", telefone)

    pattern = r"\(?(\d\d)\)?(\d?\d\d\d\d)-?(\d\d\d\d)"
    match = re.match(pattern, telefone)
    if not match:
        return None
    return f"({match.group(1)}) {match.group(2)}-{match.group(3)}"


def parse_polo(env_polo: str) -> str:
    """ Remove patterns indesejadas do polo do envolvido

    Args:
        env_polo: Polo do envolvido

    Returns:
        Polo limpo e padronizado
    """
    if env_polo is None:
        return None

    env_polo = re.sub("^POLO", "", re.sub(r"\d", "", re.sub(r"\(.+\)", "", env_polo.upper().strip())))
    env_polo = re.sub(r"[\|\\!?\[\]\{\}\(\);:\.,'\–\-\+\"\…\“\”º]", "", env_polo)
    env_polo = re.sub(" +", " ", env_polo).strip(" ")
    env_polo = "OUTROS" if env_polo == "TERCEIRO" else env_polo
    env_polo = "REP" if env_polo == "ADVOGADO" else env_polo

    if env_polo not in POLOS:
        if env_polo not in {"DESCONHECIDO", "NENHUM"}:
            print(f"env_polo desconhecido: {env_polo}")
        return None
    return env_polo


def parse_tipo(env_tipo: str) -> str:
    """ Remove patterns indesejadas do tipo do envolvido

    Args:
        env_tipo: tipo do envolvido

    Returns:
        tipo limpo
    """
    if env_tipo is None:
        return None

    env_tipo = re.sub("^PARTE", "", re.sub(r"\d", "", re.sub(r"\(.+\)", "", env_tipo.upper().strip())))
    env_tipo = re.sub(r"[\|\\!?\[\]\{\}\(\);:\.,'\–\-\+\_\"\…\“\”º]", "", env_tipo)
    env_tipo = re.sub(" +", " ", env_tipo).rstrip("S").strip(" ")

    if env_tipo not in TIPOS:
        print(f"env_tipo desconhecido: {env_tipo}")
        return None
    return env_tipo


def parse_nome(env_nome: str, rem_comp_indent: bool = False) -> str:
    """ Remove patterns indesejadas do nome do envolvido

    Args:
        env_nome: nome do envolvido
        rem_comp_indent: remove terminadores de nome comuns a companhias, (S/A, LTDA...)

    Returns:
        nome limpo
    """
    if env_nome is None:
        return None

    env_nome = env_nome.lower().strip()
    if rem_comp_indent:
        bad_ending = [r" s\.a\.$", r" s\.a$", r" s\/a$", r" sa$",
                    r" l\.t\.d\.a\.$", r" l\.t\.d\.a$", r" ltda$"]
        for end in bad_ending:
            env_nome = re.sub(end, "", env_nome)

    env_nome = re.sub(r"[\|\\!?\[\]\{\}\(\);:\.,'\–\-\+\_\"\…\“\”]", "", env_nome)
    env_nome = re.sub(" +", " ", env_nome).strip(" ").rstrip("s")
    return env_nome.title()


def parse_env_data(env_polo: str, env_tipo: str, env_nome: str) -> tuple[Literal['ATIVO/PASSIVO', 'ATIVO', 'PASSIVO', 'REP', 'OUTROS'], str, str]:
    """ Dado as informações de um envolvido, limpa e determina os dados da pessoa

    Args:
        env_polo: polo do envolvido
        env_tipo: tipo do envolvido
        env_nome: nome do envolvido

    Return:
        parsed_polo, parsed_tipo, parsed_nome
    """
    env_polo = parse_polo(env_polo)
    env_tipo = parse_tipo(env_tipo)
    env_nome = parse_nome(env_nome)

    if env_polo in POLOS:
        return env_polo, env_tipo, env_nome

    if env_tipo is None:
        return env_polo, env_tipo, env_nome

    for polo, words in POLO_TIPOS.items():
        if env_tipo in words:
            return polo, env_tipo, env_nome
    return None, env_tipo, env_nome
