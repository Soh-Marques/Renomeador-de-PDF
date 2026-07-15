import os
import re
import time
import logging
from datetime import datetime

import pytesseract
from pdf2image import convert_from_path

# ==========================================================
# CONFIGURAÇÕES
# ==========================================================

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

POPPLER_PATH = r"C:\poppler\Library\bin"

DPI = 300
LANG = "por"
PSM = 6

MODO_TESTE = False

PASTA_LOGS = "logs"
PASTA_RELATORIOS = "relatorios"

os.makedirs(PASTA_LOGS, exist_ok=True)
os.makedirs(PASTA_RELATORIOS, exist_ok=True)

# ==========================================================
# LOG
# ==========================================================

logging.basicConfig(
    filename=os.path.join(
        PASTA_LOGS,
        f"log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    ),
    level=logging.INFO,
    encoding="utf-8",
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# ==========================================================
# BANNER
# ==========================================================

def banner():

    print("=" * 60)
    print("             RENOMEADOR DE PDFs OCR")
    print("=" * 60)
    print("Autor: Solange Marques")
    print("=" * 60)
    print()


# ==========================================================
# LIMPAR NOME
# ==========================================================

def limpar_nome(texto):

    texto = re.sub(r'[\\/*?:"<>|]', "-", texto)

    texto = re.sub(r"\s+", " ", texto)

    return texto.strip()


# ==========================================================
# EXTRAIR Nº DA ORDEM
# ==========================================================

def extrair_numero(texto):

    padroes = [

        r"N[º°oO]?\s*da\s*Ordem\s*[:\-]?\s*([\d/.-]+)",

        r"N[º°oO]?\s*Ordem\s*[:\-]?\s*([\d/.-]+)",

        r"Ordem\s*[:\-]?\s*([\d/.-]+)"

    ]

    for padrao in padroes:

        resultado = re.search(

            padrao,

            texto,

            flags=re.IGNORECASE

        )

        if resultado:

            numero = resultado.group(1)

            numero = numero.replace("/", "-")

            numero = numero.replace("\\", "-")

            numero = numero.replace(".", "-")

            return numero

    return None


# ==========================================================
# EXTRAIR CREDOR
# ==========================================================

def extrair_credor(texto):

    padroes = [

        r"Credor\s*:\s*\d+\s*(.+)",

        r"Credor\s*:\s*(.+)",

    ]

    for padrao in padroes:

        resultado = re.search(

            padrao,

            texto,

            flags=re.IGNORECASE

        )

        if resultado:

            credor = resultado.group(1)

            credor = credor.split("\n")[0]

            credor = limpar_nome(credor)

            return credor

    return None


# ==========================================================
# OCR DA PRIMEIRA PÁGINA
# ==========================================================

def extrair_texto(pdf):

    imagens = convert_from_path(

        pdf,

        dpi=DPI,

        poppler_path=POPPLER_PATH

    )

    imagem = imagens[0]

    texto = pytesseract.image_to_string(

        imagem,

        lang=LANG,

        config=f"--psm {PSM}"

    )

    return texto


# ==========================================================
# GERAR NOME
# ==========================================================

def gerar_nome(texto):

    numero = extrair_numero(texto)

    credor = extrair_credor(texto)

    if numero is None:

        return None

    if credor:

        return f"Ordem_{numero}_{credor}.pdf"

    return f"Ordem_{numero}.pdf"


# ==========================================================
# CONTAR PDFs
# ==========================================================

def contar_pdfs(pasta):

    total = 0

    for _, _, arquivos in os.walk(pasta):

        for arquivo in arquivos:

            if arquivo.lower().endswith(".pdf"):

                total += 1

    return total


# ==========================================================
# PROCESSAR PASTA
# ==========================================================

def processar_pasta(pasta):

    inicio = time.time()

    total = contar_pdfs(pasta)

    contador = 0

    renomeados = 0

    erros = 0

    duplicados = 0

    nao_encontrados = 0

    lista_duplicados = []

    lista_erros = []

    lista_sem_numero = []

    print()

    print(f"📄 PDFs encontrados: {total}")

    print()

    for raiz, _, arquivos in os.walk(pasta):

        for arquivo in arquivos:

            if not arquivo.lower().endswith(".pdf"):

                continue

            contador += 1

            caminho = os.path.join(raiz, arquivo)

            print("-" * 60)

            print(f"[{contador}/{total}] {arquivo}")

            try:

                texto = extrair_texto(caminho)

                novo_nome = gerar_nome(texto)

                if novo_nome is None:

                    nao_encontrados += 1

                    lista_sem_numero.append(arquivo)

                    print("⚠ Número da ordem não encontrado.")

                    continue
                
                novo_caminho = os.path.join(raiz, novo_nome)

                # ======================================================
                # VERIFICAR SE JÁ ESTÁ RENOMEADO
                # ======================================================

                if arquivo == novo_nome:

                    print("ℹ Arquivo já está renomeado.")

                    continue

                # ======================================================
                # DUPLICADO
                # ======================================================

                if os.path.exists(novo_caminho):

                    duplicados += 1

                    lista_duplicados.append(
                        {
                            "arquivo_original": arquivo,
                            "nome_duplicado": novo_nome
                        }
                    )

                    print("⚠ Arquivo duplicado.")

                    print(f"Já existe: {novo_nome}")

                    logging.warning(
                        f"DUPLICADO -> {arquivo} -> {novo_nome}"
                    )

                    continue

                # ======================================================
                # RENOMEAR
                # ======================================================

                if MODO_TESTE:

                    print("🧪 MODO TESTE")

                    print(f"Seria renomeado para:")

                    print(novo_nome)

                    logging.info(
                        f"TESTE -> {arquivo} -> {novo_nome}"
                    )

                else:

                    os.rename(caminho, novo_caminho)

                    print("✔ Renomeado")

                    print(novo_nome)

                    logging.info(
                        f"RENOMEADO -> {arquivo} -> {novo_nome}"
                    )

                renomeados += 1

            except Exception as erro:

                erros += 1

                lista_erros.append(arquivo)

                print()

                print("❌ ERRO")

                print(arquivo)

                print()

                print(str(erro))

                logging.exception(
                    f"Erro no arquivo {arquivo}"
                )

    # ======================================================
    # TEMPO
    # ======================================================

    tempo = time.time() - inicio

    minutos = int(tempo // 60)

    segundos = int(tempo % 60)

    # ======================================================
    # RELATÓRIO
    # ======================================================

    nome_relatorio = os.path.join(

        PASTA_RELATORIOS,

        f"relatorio_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

    )

    with open(

        nome_relatorio,

        "w",

        encoding="utf-8"

    ) as relatorio:

        relatorio.write("=" * 60 + "\n")

        relatorio.write("RELATÓRIO DE EXECUÇÃO\n")

        relatorio.write("=" * 60 + "\n\n")

        relatorio.write(
            f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n\n"
        )

        relatorio.write(f"Pasta: {pasta}\n\n")

        relatorio.write(f"PDFs encontrados : {total}\n")

        relatorio.write(f"Renomeados       : {renomeados}\n")

        relatorio.write(f"Duplicados       : {duplicados}\n")

        relatorio.write(f"Sem número       : {nao_encontrados}\n")

        relatorio.write(f"Erros            : {erros}\n")

        relatorio.write(
            f"Tempo            : {minutos}m {segundos}s\n\n"
        )

        relatorio.write("=" * 60 + "\n")

        relatorio.write("ARQUIVOS DUPLICADOS\n")

        relatorio.write("=" * 60 + "\n\n")

        if lista_duplicados:

            for item in lista_duplicados:

                relatorio.write(
                    f"{item['arquivo_original']}  -->  {item['nome_duplicado']}\n"
                )

        else:

            relatorio.write("Nenhum.\n")

        relatorio.write("\n")

        relatorio.write("=" * 60 + "\n")

        relatorio.write("ARQUIVOS SEM NÚMERO DA ORDEM\n")

        relatorio.write("=" * 60 + "\n\n")

        if lista_sem_numero:

            for item in lista_sem_numero:

                relatorio.write(item + "\n")

        else:

            relatorio.write("Nenhum.\n")

        relatorio.write("\n")

        relatorio.write("=" * 60 + "\n")

        relatorio.write("ARQUIVOS COM ERRO\n")

        relatorio.write("=" * 60 + "\n\n")

        if lista_erros:

            for item in lista_erros:

                relatorio.write(item + "\n")

        else:

            relatorio.write("Nenhum.\n")
            # === PROCESSAMENTO PRINCIPAL ===

        relatorio.write("\n")

        relatorio.write("=" * 60 + "\n")
        relatorio.write("FIM DO RELATÓRIO\n")
        relatorio.write("=" * 60 + "\n")

    # ======================================================
    # RESUMO
    # ======================================================

    print("\n")
    print("=" * 60)
    print("                PROCESSO FINALIZADO")
    print("=" * 60)

    print(f"📁 Pasta analisada : {pasta}")
    print(f"📄 PDFs encontrados: {total}")
    print(f"✔ Renomeados      : {renomeados}")
    print(f"⚠ Duplicados      : {duplicados}")
    print(f"🔎 Sem nº Ordem   : {nao_encontrados}")
    print(f"❌ Erros          : {erros}")
    print(f"⏱ Tempo          : {minutos}m {segundos}s")

    print("=" * 60)

    # ======================================================
    # MOSTRAR DUPLICADOS
    # ======================================================

    if lista_duplicados:

        print("\nArquivos duplicados:")

        for item in lista_duplicados:

            print(
                f" • {item['arquivo_original']}  →  {item['nome_duplicado']}"
            )

    # ======================================================
    # MOSTRAR PDFs SEM Nº
    # ======================================================

    if lista_sem_numero:

        print("\nPDFs onde o Nº da Ordem não foi encontrado:")

        for item in lista_sem_numero:

            print(f" • {item}")

    # ======================================================
    # MOSTRAR ERROS
    # ======================================================

    if lista_erros:

        print("\nArquivos com erro:")

        for item in lista_erros:

            print(f" • {item}")

    print()
    print(f"📄 Relatório salvo em:")
    print(nome_relatorio)

    return


# ==========================================================
# LOOP PRINCIPAL
# ==========================================================

def main():

    banner()

    while True:

        pasta = input(
            "Digite o caminho da pasta raiz: "
        ).strip('"').strip()

        print()

        # ===============================================

        if not os.path.exists(pasta):

            print("❌ A pasta informada não existe.\n")

            continue

        # ===============================================

        processar_pasta(pasta)

        print()
        print("=" * 60)

        resposta = input(
            "Deseja renomear outra pasta? [S/N]: "
        ).strip().upper()

        while resposta not in ("S", "N"):

            resposta = input(
                "Digite apenas S ou N: "
            ).strip().upper()

        if resposta == "N":

            break

        print()

        banner()

    print()
    print("=" * 60)
    print("Obrigado por utilizar o Renomeador de PDFs!")
    print("=" * 60)

    input("\nPressione ENTER para sair...")


# ==========================================================
# INÍCIO
# ==========================================================

if __name__ == "__main__":
    main()
