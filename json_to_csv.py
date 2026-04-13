import pandas as pd
import json
import re
from html import unescape

def limpar_html(texto):
    if not texto:
        return ""
    texto = unescape(texto)  # remove entidades HTML (&nbsp; etc)
    texto = re.sub(r"<.*?>", "", texto)  # remove tags HTML
    texto = texto.replace("\n", " ").replace("\r", " ")
    return texto.strip()

def limpar_preco(preco):
    if not preco:
        return None
    preco = preco.replace("R$", "").replace(".", "").replace(",", ".").strip()
    try:
        return float(preco)
    except:
        return None

def json_para_csv(arquivo_json, arquivo_csv):
    with open(arquivo_json, "r", encoding="utf-8") as f:
        data = json.load(f)

    df = pd.DataFrame(data)

    # Limpeza
    if "description" in df.columns:
        df["description"] = df["description"].apply(limpar_html)

    if "price" in df.columns:
        df["price"] = df["price"].apply(limpar_preco)

    # Remove colunas completamente vazias
    df = df.dropna(axis=1, how="all")

    # Remove espaços extras em strings
    for col in df.select_dtypes(include="object").columns:
        df[col] = df[col].map(lambda x: x.strip() if isinstance(x, str) else x)

    # Salva
    df.to_csv(arquivo_csv, index=False, encoding="utf-8-sig")

    print(f"✅ CSV limpo salvo em: {arquivo_csv}")


if __name__ == "__main__":
    json_para_csv("/home/shak/code/nat_data/produtos_revista.json", "./data/produtos_revista.csv")
