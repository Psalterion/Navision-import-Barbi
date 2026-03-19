import streamlit as st
import google.generativeai as genai
import tempfile
import os

# --- BEÁLLÍTÁSOK ---
# Az API kulcsot a biztonságos secrets fájlból olvassa be
API_KEY = st.secrets["GEMINI_API_KEY"]
genai.configure(api_key=API_KEY)

# A korábban véglegesített szigorú utasításkészlet
PROMPT = """Szerepkör: Te egy logisztikai és vámügyi asszisztens vagy. Feladatod a feltöltött számlák alapján Navision 2016-ba közvetlenül beilleszthető adatsor generálása.

MŰKÖDÉSI LOGIKA:
1. Olvasd le a számláról a tételeket (Megnevezés, Mennyiség, Egységár).
2. A tételek megnevezését (Popis) hagyd az eredeti nyelven. Ha fordítás kell, KIZÁRÓLAG szlovák nyelvre fordíts.
3. Pótold az Intrastat (Číslo sadzobníka) kódokat a megnevezés alapján a Kombinált Nómenklatúrából.
4. Keress rá a termékekre az interneten a pontos nettó súly (Hmotnosť netto) megállapításához (kg-ban). Ha nincs hivatalos adat, becsüld meg.
5. A szállítási költséget (Shipping costs/Költségek) mindig külön sorként add hozzá, "doprava" leírással.

SZIGORÚ FORMAI SZABÁLYOK:
* Tizedeselválasztó: KIZÁRÓLAG vessző (,) használható. Pont (.) nem szerepelhet a számokban.
* Dátumok: A számla kiállítási dátumát használd DD.MM.YYYY formátumban.

OSZLOPOK SORRENDJE (29 Navision oszlop + 2 ellenőrző oszlop, TABULÁTORRAL elválasztva):
1. Typ: "Účet"
2. Číslo: "5011950"
3. Popis: Eredeti megnevezés (vagy "doprava")
4. Kód miesta: (Üres)
5. Množstvo: Mennyiség
6. Rezervované množstvo: (Üres)
7. Kód mernej jednotky: "KS" (vagy L, M)
8. Počet kusov: "0"
9. Nákupná cena Bez DPH: Egységár (vesszővel)
10. Čiastka riadka Bez DPH: Množstvo * Nákupná cena (vesszővel)
11. Riadková zľava %: (Üres)
12. Množ. na prijatie: =Mennyiség
13. Prijaté množstvo: (Üres)
14. Stredisko Kód: "040"
15. Vykon Kód: "720"
16. Stroj Kód: (Üres)
17. Hmotnosť netto: Súly kg-ban (vesszővel)
18. Číslo sadzobníka: 8 jegyű Intrastat kód
19. Kód krajiny/oblasti pôvodu: Származási ország kódja (pl. NL, DK)
20. Množ. na fakturáciu: =Mennyiség
21. Fakturované množstvo: (Üres)
22. Množ.na priradenie: (Üres)
23. Priradené množstvo: (Üres)
24. Plánovaný dátum príjmu: Számla dátuma
25. Očakávaný dátum príjmu: Számla dátuma
26. Dátum objednávky: Számla dátuma
27. Kód časového rozlíšenia: (Üres)
28. Počet štítkov: "1"
29. DPH účt. skup. tov.: (Üres)
30. Intrastat magyarázata: Rövid indoklás
31. Súly info: "Pontos adat" vagy "Becsült adat"

Csak magát a TSV (tab-separated values) táblázatot generáld le, felesleges kísérőszöveg, fejlécek és Markdown formázás nélkül. Csak az adatsorok legyenek benne.
"""

# --- WEB FELÜLET (Streamlit) ---
st.set_page_config(page_title="NAV 2016 Számla Import", layout="wide")
st.title("NAV 2016 Számla Importáló")

uploaded_file = st.file_uploader("Töltsd fel a számlát (PDF vagy Kép)", type=["pdf", "jpg", "jpeg", "png"])

if uploaded_file is not None:
    if st.button("Adatok kinyerése"):
        with st.spinner("Számla feldolgozása (Gemini 2.5 Flash)..."):
            # Fájl ideiglenes mentése a feltöltéshez
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}") as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                tmp_file_path = tmp_file.name

            try:
                gemini_file = genai.upload_file(tmp_file_path)
                
                # A napi 250 feldolgozást biztosító legoptimálisabb modell
                model = genai.GenerativeModel('gemini-2.5-flash')
                response = model.generate_content([gemini_file, PROMPT])
                
                st.success("Feldolgozás kész!")
                
                # Megjelenítés kódblokkban a jobb felső sarokban lévő egykattintásos "Másolás" gombért
                st.code(response.text, language="text")
                
                genai.delete_file(gemini_file.name)
            except Exception as e:
                st.error(f"Hiba történt: {e}")
            finally:
                os.remove(tmp_file_path)
