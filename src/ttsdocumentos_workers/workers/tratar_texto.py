from aio_pika.abc import AbstractIncomingMessage
from ttsdocumentos_core.domiain.workers.transcribe_text_dto import TranscribeTextDTO
from ttsdocumentos_core.domiain.workers.treat_text_dto import TreatTextDTO
from ttsdocumentos_core.log.log_maneger import LogLevels, LoggerManager, LoggerNames
from ttsdocumentos_core.rabbitmq.rabbitmq import RabbitMQConnection, RabbitMQProducer
import panflute as pf

logger = LoggerManager(nome=LoggerNames.WORKER, level=LogLevels.DEBUG)
async def processar_tratar_texto(message: AbstractIncomingMessage):
    payload = TreatTextDTO.from_json(message.body.decode())
    logger.info(f"Tratando texto do documento")
    doc = doc = pf.convert_text(
        text=payload.conteudo, 
        input_format="markdown", 
        output_format="panflute", 
        standalone=True)
    logger.info("Sucesso")
    narracao = []
    for elem in doc.content:
        txt = process_block(elem)
        if txt:
            narracao.append(txt)

    conteudo = "\n".join(narracao)
    return TranscribeTextDTO(
        conteudo=conteudo,
        name_file=payload.name_file,
        language=payload.language
    )

async def processar_tratar_texto_wrapper(msg, connection: RabbitMQConnection):
    # Aqui você processa a mensagem
    result = await processar_tratar_texto(msg)

    producer = RabbitMQProducer(connection)
    await producer.setup_exchange()
    await producer.bind_queue(TranscribeTextDTO.QUEUE_NAME, "transcribe_text_routing_key")
    await producer.publishJson(result.to_dict(), routing_key="transcribe_text_routing_key")

def process_block(elem: pf.Element) -> str:
    """
    Converte um bloco (Header, Para, BulletList, Table, etc.) em texto narrável.
    """
    if isinstance(elem, pf.Header):
        level = elem.level
        return f"Título nível {level}: {pf.stringify(elem)}"

    elif isinstance(elem, pf.Para):
        return pf.stringify(elem)

    elif isinstance(elem, pf.Plain):
        return pf.stringify(elem)

    elif isinstance(elem, pf.BulletList):
        itens = []
        for li in elem.content:
            txt = " ".join(process_block(b) for b in li.content if b)
            itens.append(f"Item da lista: {txt}")
        return "\n".join(itens)

    elif isinstance(elem, pf.OrderedList):
        itens = []
        for idx, li in enumerate(elem.content, start=1):
            txt = " ".join(process_block(b) for b in li.content if b)
            itens.append(f"Item {idx}: {txt}")
        return "\n".join(itens)

    elif isinstance(elem, pf.Table):
        return describe_table(elem)

    elif isinstance(elem, pf.CodeBlock):
        return "[bloco de código omitido]"

    elif isinstance(elem, pf.Image):
        alt = pf.stringify(elem)
        return f"[imagem: {alt}]"

    # Outros tipos podem ser adicionados aqui conforme necessário
    return ""


def describe_table(tbl: pf.Table) -> str:
    """
    Retorna uma descrição narrável de uma tabela Panflute 2.x
    compatível com Pandoc 2.x.
    Trata cabeçalho, corpo, rodapé e legenda,
    concatena células multilinha e evita erros de atributos ausentes.
    """
    descr = ["Tabela:"]

    # Legenda
    if getattr(tbl, "caption", None):
        descr.append("Legenda: " + pf.stringify(tbl.caption))

    def get_cell_text(cell):
        if getattr(cell, "content", None):
            return " ".join(pf.stringify(el) for el in cell.content)
        return ""

    # Cabeçalho (primeira linha do conteúdo) será usado como nomes das colunas, se existir
    header_names = []
    if getattr(tbl, "content", None) and len(tbl.content) > 0:
        first_row = tbl.content[0]
        header_names = [get_cell_text(cell) for cell in getattr(first_row, "content", [])]

    # Percorre todas as linhas da tabela
    for i, row in enumerate(getattr(tbl, "content", []), start=1):
        cells = getattr(row, "content", [])
        if any(get_cell_text(c) for c in cells):
            cell_texts = []
            for j, cell in enumerate(cells):
                col_name = header_names[j] if j < len(header_names) and header_names[j] else f"Coluna {j+1}"
                cell_texts.append(f'coluna "{col_name}": {get_cell_text(cell)}')
            descr.append(f"Linha {i}: " + ", ".join(cell_texts))

    # Rodapé
    if getattr(tbl, "foot", None) and getattr(tbl.foot, "content", None):
        for row in tbl.foot.content:
            row_text = [get_cell_text(cell) for cell in getattr(row, "content", [])]
            if any(row_text):
                descr.append("Rodapé: " + " | ".join(row_text))

    return " ".join(descr)

