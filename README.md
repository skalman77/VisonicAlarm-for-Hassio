# Visonic Alarm för Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg?style=for-the-badge)](https://github.com/custom-components/hacs)
[![Buy Me A Coffee](https://img.shields.io/badge/Buy%20Me%20A%20Coffee-Donate-yellow.svg?style=for-the-badge)](https://www.buymeacoffee.com/4nd3rs)

Visonic/Bentel/Tyco Alarm System integration för Home Assistant med GUI-konfiguration.

![Alarm Dialog](HomeAssistantArmDialog2.png)

## Översikt

Denna integration gör att du kan styra ditt Visonic-larmsystem direkt från Home Assistant. Den ansluter till API-servern som används av Visonic-GO och BW-apparna.

### Funktioner

- 🔐 **Alarm Control Panel** - Larma och avlarma ditt system
- 🚪 **Dörr/Fönster-sensorer** - Se status på alla dina kontakter
- 🏠 **Home och Away-lägen** - Stöd för olika larmlägen
- 🔢 **PIN-kod stöd** - Valfri PIN-kod för säkerhet
- ⚙️ **GUI-konfiguration** - Enkel setup utan YAML

### Kompatibilitet

Testad med:
- Visonic PowerMaster 10 med PowerLink 3
- Visonic PowerMaster 30

Bör fungera med de flesta Visonic/Bentel/Tyco-system som använder Visonic-GO eller BW-appen.

## Installation

### Via HACS (Rekommenderat)

1. Öppna HACS i Home Assistant
2. Gå till **Integrations**
3. Klicka på **⋮** (tre prickar uppe till höger)
4. Välj **Custom repositories**
5. Lägg till: `https://github.com/skalman77/VisonicAlarm-for-Hassio`
6. Välj kategori: **Integration**
7. Klicka **Add**
8. Sök efter **Visonic Alarm**
9. Klicka **Download**
10. Starta om Home Assistant

### Manuell installation

1. Ladda ner den senaste versionen från [Releases](https://github.com/skalman77/VisonicAlarm-for-Hassio/releases)
2. Kopiera mappen `custom_components/visonicalarm` till din `config/custom_components/` katalog
3. Starta om Home Assistant

## Konfiguration

**OBS!** Denna integration konfigureras via GUI, inte YAML.

### Steg 1: Samla information

Du behöver följande uppgifter (samma som du använder i Visonic-GO/BW-appen):

- **Värdnamn** (host): t.ex. `company.tycomonitor.com`
- **Panel-ID**: Hittas i din app
- **Användarkod**: Din Master User PIN-kod
- **App-ID**: Generera ett UUID på [uuidgenerator.net](https://www.uuidgenerator.net/)
- **E-post**: Din Visonic-kontots e-post
- **Lösenord**: Ditt Visonic-kontots lösenord
- **Partition**: `-1` (standard för de flesta system)

### Steg 2: Lägg till integration

1. Gå till **Inställningar** → **Enheter & tjänster**
2. Klicka **+ Lägg till integration**
3. Sök efter **Visonic Alarm**
4. Fyll i formuläret med uppgifterna ovan
5. Klicka **Skicka**

### Steg 3: Konfigurera inställningar (valfritt)

Efter installation kan du ändra vissa inställningar:

1. Gå till **Enheter & tjänster**
2. Hitta **Visonic Alarm**
3. Klicka **Konfigurera**
4. Ändra:
   - **Ingen PIN krävs**: Hoppa över PIN-kod vid larmning/avlarmning
   - **Händelse tim-offset**: Justera tidszon för händelseloggen

## Användning

### Entiteter

Efter konfiguration skapas följande entiteter:

#### Alarm Control Panel
- `alarm_control_panel.visonic_alarm`

**States:**
- `disarmed` - Avlarmat
- `armed_home` - Hemmalarm
- `armed_away` - Bortalarm  
- `arming` - Larmar
- `pending` - Väntläge (ingångsfördröjning)
- `triggered` - Utlöst

#### Binary Sensors (Kontakter)
- `binary_sensor.visonic_alarm_contact_1`
- `binary_sensor.visonic_alarm_contact_2`
- osv.

**States:**
- `on` - Öppen
- `off` - Stängd

### Automationer

```yaml
automation:
  # Larma när alla lämnar
  - alias: "Autolarma när alla går"
    trigger:
      - platform: state
        entity_id: group.all_persons
        to: 'not_home'
        for: '00:05:00'
    action:
      - service: alarm_control_panel.alarm_arm_away
        target:
          entity_id: alarm_control_panel.visonic_alarm
        data:
          code: '1234'

  # Avlarma när någon kommer hem
  - alias: "Avlarma när någon kommer hem"
    trigger:
      - platform: state
        entity_id: group.all_persons
        to: 'home'
    condition:
      - condition: state
        entity_id: alarm_control_panel.visonic_alarm
        state: 'armed_away'
    action:
      - service: alarm_control_panel.alarm_disarm
        target:
          entity_id: alarm_control_panel.visonic_alarm
        data:
          code: '1234'

  # Notifiering om dörr öppnas när larmat
  - alias: "Notifiera om dörr öppnas när larmat"
    trigger:
      - platform: state
        entity_id: binary_sensor.visonic_alarm_contact_1
        to: 'on'
    condition:
      - condition: state
        entity_id: alarm_control_panel.visonic_alarm
        state: 'armed_away'
    action:
      - service: notify.mobile_app
        data:
          message: "Varning! Dörr öppnades när systemet var larmat!"
```

### Lovelace-kort

```yaml
type: alarm-panel
entity: alarm_control_panel.visonic_alarm
states:
  - arm_away
  - arm_home
```

## Felsökning

### Problem: Integrationen visas inte i listan

**Lösning:**
- Kontrollera att filerna ligger i rätt katalog: `config/custom_components/visonicalarm/`
- Starta om Home Assistant
- Kontrollera loggen för felmeddelanden

### Problem: Kan inte ansluta till larmsystemet

**Lösning:**
- Verifiera att uppgifterna är korrekta (testa i Visonic-appen först)
- Kontrollera att användaren är **Master User** i systemet
- Dubbelkolla värdnamnet (samma som i appen)
- Kontrollera internetanslutning

### Problem: Sensorer visas inte

**Lösning:**
- Kontrollera att zonerna är aktiverade i larmsystemet
- Vänta 10-30 sekunder efter konfiguration
- Starta om Home Assistant
- Kontrollera loggen för felmeddelanden

### Problem: PIN-kod accepteras inte

**Lösning:**
- Verifiera att `user_code` är samma som din Master User PIN
- Kontrollera att du inte har stavfel i konfigurationen
- Om "Ingen PIN krävs" är aktiverat behövs ingen kod

## Migrera från YAML

Om du tidigare använde YAML-konfiguration:

1. **Backup** - Säkerhetskopiera din `configuration.yaml`

2. **Ta bort YAML-konfiguration:**
```yaml
# TA BORT DETTA FRÅN configuration.yaml:
visonicalarm:
  host: YOURALARMCOMPANY.tycomonitor.com
  panel_id: 123456
  # etc...
```

3. **Starta om** Home Assistant

4. **Konfigurera via GUI** enligt instruktionerna ovan

**OBS!** Dina entiteter behåller samma entity_id, så dina automationer bör fortsätta fungera.

## Kända begränsningar

- Endast partition `-1` (standard) stöds per integration-instans
- Larmsystemet pollas var 10:e sekund (samma som appen)
- Kräver Master User-behörighet

## Support

Om du stöter på problem:

1. Kontrollera [GitHub Issues](https://github.com/skalman77/VisonicAlarm-for-Hassio/issues)
2. Kolla Home Assistant-loggen: **Inställningar** → **System** → **Loggar**
3. Skapa en ny issue med:
   - Home Assistant-version
   - Felmeddelande från loggen
   - Steg för att återskapa problemet

## Bidrag

Pull requests är välkomna! För större ändringar, öppna gärna en issue först för att diskutera vad du vill ändra.

## Licens

[MIT](LICENSE)

## Tack till

- Ursprunglig integration av [@And3rsL](https://github.com/And3rsL)
- Python-biblioteket [VisonicAlarm2](https://github.com/And3rsL/VisonicAlarm2)

## Ansvarsfriskrivning

**VIKTIGT:** Denna integration är INTE officiellt stödd av Visonic, Bentel eller Tyco. Den använder deras opublicerade REST API. Jag tar inget ansvar för förlust eller skada som kan uppstå från användning av denna integration.

Använd på egen risk.

---

[![Buy Me A Coffee](https://cdn.buymeacoffee.com/buttons/default-black.png)](https://www.buymeacoffee.com/4nd3rs)

Om du gillar denna integration, överväg att stödja den ursprungliga utvecklaren!