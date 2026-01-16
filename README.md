# 🔥 WiNet Stove – Home Assistant Integration

Integrazione Home Assistant per stufe a pellet **WiNet**  
Supporta **connessione Locale e Cloud**.

---

## ✨ Funzionalità

- Accensione / Spegnimento stufa
- Impostazione potenza (1–5)
- Temperatura aria (step 0.5°C)
- Temperatura acqua (opzionale)
- Sensori:
  - Stato stufa
  - Temperatura aria
  - Temperatura fumi
  - RPM estrattore
- Scritture **debounced** (protezione memoria interna)
- Wizard di configurazione semplice

---

## 🔧 Installazione (HACS)

1. HACS → Integrazioni → **Custom repository**
2. URL: https://github.com/TUOUSERNAME/winet-ha
3. Categoria: **Integration**
4. Installa **WiNet Stove**
5. Riavvia Home Assistant
6. Aggiungi integrazione da **Impostazioni → Dispositivi**

---

## 🧭 Configurazione

### Modalità Locale
- Inserisci IP della stufa (es. `192.168.1.50`)
- Seleziona se la stufa è **ad acqua**

### Modalità Cloud
- Inserisci `stove_id`
- Seleziona se la stufa è **ad acqua**

---

## 🌡️ Note sulle temperature
Le stufe WiNet usano **mezzi gradi (0.5°C)**.  
L’integrazione converte automaticamente i valori.

---

## 🧑‍💻 Supporto
Questa è una integrazione **non ufficiale**.  
Segnalazioni e contributi sono benvenuti!

---

## 📜 Licenza
MIT

