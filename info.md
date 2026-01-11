# Visonic Alarm Integration

Visonic/Bentel/Tyco Alarm System integration för Home Assistant med GUI-konfiguration.

## ✨ Funktioner

- 🔐 Larmkontrollpanel för att larma/avlarma systemet
- 🚪 Sensorer för alla dörr- och fönsterkontakter
- 🏠 Stöd för både Home och Away-lägen
- 🔢 Valfri PIN-kod för larmning/avlarmning
- ⚙️ GUI-konfiguration (inga YAML-filer behövs)

## 📋 Krav

- Visonic/Bentel/Tyco larmsystem med PowerLink-modul
- Visonic-GO eller BW-app med fungerande konto
- Master User-behörighet i systemet

## 🚀 Installation

### Steg 1: Installera via HACS
1. Öppna HACS i Home Assistant
2. Gå till **Integrations**
3. Klicka på **⋮** (tre prickar) → **Custom repositories**
4. Lägg till: `https://github.com/skalman77/VisonicAlarm-for-Hassio`
5. Kategori: **Integration**
6. Klicka **Add**
7. Sök efter **Visonic Alarm** och klicka **Download**
8. Starta om Home Assistant

### Steg 2: Konfigurera integrationen
1. Gå till **Inställningar** → **Enheter & tjänster**
2. Klicka **+ Lägg till integration**
3. Sök efter **Visonic Alarm**
4. Fyll i formuläret:

| Fält | Beskrivning | Exempel |
|------|-------------|---------|
| **Värdnamn** | Din alarm-servers adress | `company.tycomonitor.com` |
| **Panel-ID** | Panel-ID från din app | `123456` |
| **Användarkod** | Din PIN-kod för larmet | `1234` |
| **App-ID** | UUID (generera på uuidgenerator.net) | `00000000-0000-0000-0000-000000000000` |
| **E-post** | Din Visonic-kontots e-post | `exempel@email.com` |
| **Lösenord** | Ditt Visonic-kontots lösenord | `dittlösenord` |
| **Partition** | Larmzon (-1 för standard) | `-1` |
| **Ingen PIN krävs** | Hoppa över PIN vid larmning | `false` |
| **Händelse tim-offset** | Tidszonsjustering | `0` |

5. Klicka **Skicka**

## ⚙️ Inställningar

Efter installation kan du ändra vissa inställningar:
1. Gå till **Enheter & tjänster**
2. Hitta **Visonic Alarm**
3. Klicka **Konfigurera**
4. Ändra **Ingen PIN krävs** eller **Händelse tim-offset**

## 📱 Entiteter som skapas

### Alarm Control Panel
- `alarm_control_panel.visonic_alarm`
  - States: `disarmed`, `armed_home`, `armed_away`, `arming`, `pending`, `triggered`

### Binary Sensors (Kontakter)
- `binary_sensor.visonic_alarm_contact_1`
- `binary_sensor.visonic_alarm_contact_2`
- `binary_sensor.visonic_alarm_contact_X`
  - States: `on` (öppen), `off` (stängd)

## 🎯 Användning

### I Home Assistant-gränssnittet
1. Gå till **Översikt**
2. Hitta din **Visonic Alarm**-kort
3. Klicka för att larma/avlarma
4. Ange PIN-kod om aktiverat

### I automationer
```yaml
automation:
  - alias: "Larma när alla lämnar hemmet"
    trigger:
      - platform: state
        entity_id: group.all_persons
        to: 'not_home'
    action:
      - service: alarm_control_panel.alarm_arm_away
        target:
          entity_id: alarm_control_panel.visonic_alarm
        data:
          code: '1234'
```

### I skript
```yaml
script:
  arm_alarm_home:
    sequence:
      - service: alarm_control_panel.alarm_arm_home
        target:
          entity_id: alarm_control_panel.visonic_alarm
        data:
          code: '1234'
```

## 🔧 Felsökning

### Integrationen visas inte
- Kontrollera att du startat om Home Assistant efter installation
- Kolla loggen: **Inställningar** → **System** → **Loggar**

### Kan inte ansluta
- Verifiera att dina uppgifter är korrekta (testa i Visonic-appen först)
- Kontrollera att du har Master User-behörighet
- Verifiera att värdnamnet är rätt (samma som i appen)

### Sensorer visas inte
- Kontrollera att dina zoner är aktiverade i larmsystemet
- Vänta 10-30 sekunder efter konfiguration
- Starta om Home Assistant

### PIN-kod fungerar inte
- Kontrollera att `user_code` är samma som din Master User PIN
- Dubbelkolla att du skrev rätt kod i konfigurationen

## 📝 Migrera från YAML

Om du tidigare använde YAML-konfiguration:

1. **Ta bort** denna konfiguration från `configuration.yaml`:
```yaml
visonicalarm:
  host: ...
  panel_id: ...
  # etc.
```

2. Starta om Home Assistant

3. Följ installationsinstruktionerna ovan för att konfigurera via GUI

## 🆘 Support

Om du stöter på problem:
1. Kontrollera [GitHub Issues](https://github.com/skalman77/VisonicAlarm-for-Hassio/issues)
2. Skapa en ny issue om problemet inte finns listat
3. Inkludera Home Assistant-loggar och din konfiguration (dölj känslig info)

## 📜 Licens

MIT License - Se [LICENSE](LICENSE) för detaljer

## ☕ Stöd utvecklaren

Om du gillar denna integration, överväg att stödja den ursprungliga utvecklaren:

[![Buy Me A Coffee](https://cdn.buymeacoffee.com/buttons/default-black.png)](https://www.buymeacoffee.com/4nd3rs)

---

**OBS!** Denna integration är inte officiellt stödd av Visonic/Bentel/Tyco. Använd på egen risk.