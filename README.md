# 🗣️ Mi Tablero — Comunicación (CAA)

Autor / Author / Tekijä: **KALEVI LATVA AIJO ALEGRIA** · Windows · 100 % local

> 🇪🇸 Español · 🇬🇧 English · 🇫🇮 Suomi — el mismo documento en tres idiomas más abajo.

---

## 🇪🇸 Español

Un **tablero de comunicación aumentativa (CAA)**: le da voz a personas que **no pueden hablar**
(autismo no verbal, ictus/afasia, parálisis cerebral, ELA, alguien recién operado). Se tocan
**pictogramas** para armar una frase y la computadora **la dice en voz alta**.

### Tres formas de usarlo

| Versión | Voz | Palabras | Dónde corre |
|---------|-----|----------|-------------|
| 🖥️ **Tu voz en vivo** (`Tablero-mi-voz.bat`) | **Tu voz clonada** (IA) | **Cualquiera** — dice lo que sea | Tu PC con **GPU NVIDIA** |
| 📦 **Escritorio (.exe)** | Tu voz en **200 palabras** + voz del sistema para el resto | 200 + sistema | Cualquier PC (sin GPU) |
| 📱 **Teléfono (web/PWA)** | **Tu voz en 200 palabras** + voz del sistema para el resto | 200 + sistema | Móvil/tablet (navegador) |

> La **voz clonada que dice cualquier cosa** necesita GPU (por eso es tu PC). El `.exe` y el móvil
> traen **200 palabras pre-grabadas en tu voz** (core del idioma + animales, comida, lugares…) y usan
> la voz del sistema para palabras fuera de esas 200.

### Cómo usar
1. Toca los **dibujos** para armar la frase (aparece arriba).
2. Pulsa **🔊 Hablar** → dice la frase completa.
3. **⌫ Borrar** / **🗑️ Vaciar**. Cambia de **categoría** con los colores.
4. **✏️ Editar → ➕ Añadir**: crea botones propios. En la versión con tu voz en vivo, la palabra
   nueva **se genera en tu voz automáticamente** y queda guardada.

### 🎙️ Tu voz (clonación)
La app clona tu voz con **Chatterbox** (IA) a partir de una grabación (`voz_referencia.wav`).
En la versión en vivo (GPU), al pulsar Hablar genera la frase entera en tu voz y la guarda para
repetir al instante. El `.exe` y la web traen **200 palabras ya generadas en tu voz**.

**🎤 Voz de confianza:** con el botón **«Voz»** (versión en vivo) puedes **grabar** o **cargar** un
archivo de audio de una **persona de confianza** (mamá, papá, un cuidador). El tablero pasará a
hablar con **esa** voz — para que el usuario oiga una voz cercana y de confianza.

*Privacidad:* tu voz es personal; no la subas a sitios públicos si no quieres compartirla.

### 📱 Instalar en el teléfono
Publica `web/` en **GitHub Pages**, abre el enlace en el móvil y **"Añadir a pantalla de inicio"**.
Funciona sin internet (PWA).

---

## 🇬🇧 English

An **Augmentative and Alternative Communication (AAC) board**: it gives a voice to people who
**cannot speak** (non-verbal autism, stroke/aphasia, cerebral palsy, ALS, post-surgery). You tap
**pictograms** to build a sentence and the computer **speaks it out loud**.

### Three ways to use it

| Version | Voice | Words | Runs on |
|---------|-------|-------|---------|
| 🖥️ **Your live voice** (`Tablero-mi-voz.bat`) | **Your cloned voice** (AI) | **Anything** — says whatever you type | Your PC with an **NVIDIA GPU** |
| 📦 **Desktop (.exe)** | Your voice for **200 words** + system voice for the rest | 200 + system | Any PC (no GPU) |
| 📱 **Phone (web/PWA)** | **Your voice for 200 words** + system voice for the rest | 200 + system | Mobile/tablet (browser) |

> The **cloned voice that says anything** needs a GPU (hence your PC). The `.exe` and phone ship with
> **200 words pre-recorded in your voice** (language core + animals, food, places…) and use the
> system voice for words outside those 200.

### How to use
1. Tap the **pictures** to build the sentence (shown on top).
2. Press **🔊 Speak** → it says the whole sentence.
3. **⌫ Delete** / **🗑️ Clear**. Switch **categories** with the colored buttons.
4. **✏️ Edit → ➕ Add**: create your own buttons. In the live-voice version, the new word is
   **generated in your voice automatically** and saved.

### 🎙️ Your voice (cloning)
The app clones your voice with **Chatterbox** (AI) from a recording (`voz_referencia.wav`).
In the live version (GPU), Speak generates the whole sentence in your voice and caches it for
instant replay. The `.exe` and web ship with **200 words already generated in your voice**.

**🎤 A trusted voice:** the **«Voz»** button (live version) lets you **record** or **load** an
audio file of a **trusted person** (mom, dad, a caregiver). The board will then speak in **that**
voice — so the user hears a familiar, trusted voice.

*Privacy:* your voice is personal; don't upload it publicly unless you want to share it.

### 📱 Install on a phone
Publish `web/` on **GitHub Pages**, open the link on the phone and **"Add to Home Screen"**.
Works offline (PWA).

---

## 🇫🇮 Suomi

**Puhetta tukeva ja korvaava kommunikointitaulu (AAC)**: se antaa äänen ihmisille, jotka
**eivät voi puhua** (puhumaton autismi, aivohalvaus/afasia, CP-vamma, ALS, leikkauksen jälkeen).
Kosketat **kuvasymboleja** rakentaaksesi lauseen, ja tietokone **puhuu sen ääneen**.

### Kolme käyttötapaa

| Versio | Ääni | Sanat | Missä toimii |
|--------|------|-------|--------------|
| 🖥️ **Oma ääni suorana** (`Tablero-mi-voz.bat`) | **Kloonattu äänesi** (tekoäly) | **Mitä tahansa** | Oma tietokone, jossa **NVIDIA-GPU** |
| 📦 **Työpöytä (.exe)** | Oma ääni **200 sanaan** + järjestelmän ääni muille | 200 + järjestelmä | Mikä tahansa PC (ei GPU:ta) |
| 📱 **Puhelin (web/PWA)** | **Oma ääni 200 sanaan** + järjestelmän ääni muille | 200 + järjestelmä | Puhelin/tabletti (selain) |

> **Mitä tahansa sanova kloonattu ääni** tarvitsee näytönohjaimen (siksi oma tietokone). `.exe` ja
> puhelin sisältävät **200 sanaa valmiiksi äänelläsi nauhoitettuna** (kielen ydin + eläimet, ruoka,
> paikat…) ja käyttävät järjestelmän ääntä näiden 200 ulkopuolisille sanoille.

### Käyttö
1. Kosketa **kuvia** rakentaaksesi lauseen (näkyy ylhäällä).
2. Paina **🔊 Puhu** → se sanoo koko lauseen.
3. **⌫ Poista** / **🗑️ Tyhjennä**. Vaihda **kategoriaa** väripainikkeilla.
4. **✏️ Muokkaa → ➕ Lisää**: luo omia painikkeita. Suora ääni -versiossa uusi sana
   **luodaan automaattisesti äänelläsi** ja tallennetaan.

### 🎙️ Oma äänesi (kloonaus)
Sovellus kloonaa äänesi **Chatterbox**-tekoälyllä nauhoituksesta (`voz_referencia.wav`).
Suorassa versiossa (GPU) Puhu luo koko lauseen äänelläsi ja tallentaa sen välitöntä toistoa varten.
`.exe` ja web sisältävät **200 sanaa valmiiksi äänelläsi**.

**🎤 Luotettu ääni:** **«Voz»**-painikkeella (suora versio) voit **nauhoittaa** tai **ladata**
äänitiedoston **luotetulta henkilöltä** (äiti, isä, hoitaja). Taulu puhuu tämän jälkeen **sillä**
äänellä — jotta käyttäjä kuulee tutun ja turvallisen äänen.

*Yksityisyys:* äänesi on henkilökohtainen; älä lataa sitä julkisesti, ellet halua jakaa sitä.

### 📱 Asennus puhelimeen
Julkaise `web/` **GitHub Pagesissa**, avaa linkki puhelimessa ja **"Lisää aloitusnäyttöön"**.
Toimii ilman internetiä (PWA).

---

## ⚙️ Tecnología / Technology / Teknologia

- **Python** · **PySide6** (Qt 6) · **QtTextToSpeech** (voz del sistema, fallback).
- Voz clonada / Cloned voice / Kloonattu ääni: **Chatterbox** + **Whisper** + **PyTorch (CUDA)**.
- Web/PWA: HTML + clips de tu voz + `SpeechSynthesis` + Service Worker (offline).

## 🔨 Generar el .exe / Build the .exe / Luo .exe
`crear_exe.bat` → `dist\Tablero\`. Empaqueta `voz_cache` (tus 200 clips) + la voz del sistema.

---

Hecho con cariño · Made with care · Tehty huolella — **KALEVI LATVA AIJO ALEGRIA**
