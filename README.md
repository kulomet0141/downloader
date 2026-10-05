# Downloader
Tento script slouží pro stahování zpráv z určeného Discord serveru do sqlite databáze.
Počítá s použitím metody `get_all()` ze třídy `OptOutDb` z modulu `database.opt_out`, která vrátí množinu id uživatelů, kteří si nepřejí účastnit se průzkumu.

---

## Instalace
Pro funkčnost scriptu je nutné dodat balíček `database` s modulem `opt_out`, který obsahuje třídu `OptOutDb` s metodou `get_all()`, na stejné úrovni jako složka obsahující `downloader.py`.
```text
projekt/
├── database/
│   └── opt_out.py
└── downloader/
    ├── main.py
    ├── downloader.py
    └── utils.py
```
Ostatní závislosti jde nainstalovat pomocí `pip install -r requirements.txt`
Vyvíjeno v Pythonu 3.14.0

---

## Požadavky na bota
Bot musí mít na serveru oprávnění `Zobrazit kanál (View Channel)` a `Číst historii zpráv (Read Message History)`.
Downloader používá `Intents.default()` a je nutné v Discord Developer Portalu pro daného bota povolit privilegované oprávnění:
- Oprávnění obsahu zpráv (Message Content Intent)

---

## Použití
Script získává token bota z proměnné prostředí `DISCORD_TOKEN`

```bash
export DISCORD_TOKEN="..."
```
```bash
python main.py --date-from [YYYY-MM-DD] --date-to [YYYY-MM-DD] [--filter path_to_filter.json] --database [path_to_database] --server [server_id]
```

 - `--help`, `-h` zobrazí nápovědu
 - `--date-from` datum od kterého se mají stáhnout zprávy
 - `--date-to` datum do kterého se mají stáhnout zprávy
 - `--filter` cesta k souboru s filtry
 - `--database` cesta k databázi, pokud není zadána, bude použita výchozí cesta `./download.sqlite`
 - `--server` id serveru, ze kterého se mají stáhnout zprávy

### Datumy
- Data musí být zadána ve formátu `YYYY-MM-DD`
- `--date-from` musí být menší než `--date-to`
- Data z `--date-from` jsou zahrnuta do stažených dat
- Data z `--date-to` nejsou zahrnuta do stažených dat

```
--date-from <= datum zprávy < --date-to
```

### Filtrování kanálů
- V případě nepoužití `--filter` se script pokusí stáhnout zprávy ze všech kanálů na serveru.
- Při použití script zahrnuje pouze kanály, které obsahují nějaký z filtrů v souboru.
- Soubor použitý pro filtrování musí být ve formátu JSON a obsahovat pole řetězců, které jsou využívány jako filtry.
- Filtrování je podřetězcové, takže např. `["test"]` zahrne kanály `test`, `test2`, `netestuj`, atd.
- Při několikanásobném použití `--filter` se projdou všechny soubory a jednotlivé filtry se spojí do jedné množiny.
- Filtry nejsou case-sensitive

---

## Databáze
- Zprávy jsou uloženy do SQLite databáze.
- Databáze je vytvořena automaticky při spuštění scriptu.
- Databáze obsahuje tabulky `messages` a `reactions`.
- Databáze obsahuje index pro tabulku `messages`, který se používá pro zabránění duplicitních zpráv.
- Samolepky jsou přidány za text zprávy ve formátu `<sticker>název</sticker>`.
- Vlastní emoji jsou v textu vloženy do `<emoji>název</emoji>` a v tabulce reakcí je uložen pouze název emoji.

### Tabulka `messages`

| Sloupec   | Typ      | Popis                                                           |
|-----------|----------|-----------------------------------------------------------------|
| `id`      | INTEGER  | Interní identifikátor řádku (nesouvisí s ID zprávy na Discordu) |
| `channel` | TEXT     | Název kanálu, ze kterého zpráva pochází                         |
| `date`    | DATETIME | Čas odeslání zprávy, ISO 8601, UTC                              |
| `text`    | TEXT     | text zprávy                                                     |

### Tabulka `reactions`

| Sloupec      | Typ     | Popis                                 |
|--------------|---------|---------------------------------------|
| `id`         | INTEGER | Interní identifikátor řádku           |
| `message_id` | INTEGER | Odkaz na messages.id                  |
| `reaction`   | TEXT    | Emoji reakce; u vlastních emoji název |
| `count`      | INTEGER | Počet uživatelů, kteří reakci použili |


---

## Anonymizace
Script se snaží nahradit co nejvíce identifikujících informací.
Jména a přezdívky se v českém i slovenském jazyce vyskytují v mnoha tvarech a nejsou proto anonymizovány.
V textu zpráv jsou některé věci nahrazovány následovně:
- odkaz -> `<URL>`
- email -> `<EMAIL>`
- telefonní číslo -> `<PHONE>`
- zmínka uživatele -> `<USER>`
- zmínka kanálu -> `<CHANNEL>`
- zmínka role -> `<ROLE>`
- osobní číslo -> `000000`
- xlogin -> `xlogin00`

---

## Opt-out
Script počítá s přístupem k databázi obsahující id uživatelů, kteří si nepřejí, aby jejich zprávy byly zahrnuty do stažených dat.
Zprávy a reakce na zprávy od těchto uživatelů jsou při stahování přeskočeny.

---

## Omezení
- Script nestahuje vlákna, obrázky ani neumí ukládat použité příkazy, které se neukládají do historie zpráv.
- Z důvodu množství různých tvarů jmen a přezdívek se nepokouší o jejich odstranění.
- Některé filtry mohou zachytit více věcí, než je určeno. 
Příkladem je jakékoliv šestimístné číslo, které bude zachyceno filtrem pro osobní číslo.
- Systémové zprávy se neukládají
- Při opakovaném stahování se počty reakcí neaktulizují
