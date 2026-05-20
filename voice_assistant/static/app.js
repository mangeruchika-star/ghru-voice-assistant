const state = {
  language: "en",
  phase: "language",
  isBusy: false,
  isListening: false,
  recognition: null,
  hasStarted: false,
};

const transcriptEl = document.getElementById("transcript");
const statusBarEl = document.getElementById("statusBar");
const startButtonEl = document.getElementById("startButton");
const micButtonEl = document.getElementById("micButton");
const langSwapButtonEl = document.getElementById("langSwapButton");
const exitButtonEl = document.getElementById("exitButton");
const composerEl = document.getElementById("composer");
const queryInputEl = document.getElementById("queryInput");
const sendButtonEl = document.getElementById("sendButton");
const assistantPaneEl = document.getElementById("assistantPane");
const avatarEl = document.getElementById("avatar");
const shellEl = document.getElementById("shell");
let audioOutputPrimed = false;
const SERVER_TTS_TIMEOUT_MS = 12000;
let activeAudio = null;

function stopAllSpeech() {
  if (activeAudio) {
    try {
      activeAudio.pause();
      activeAudio.currentTime = 0;
    } catch (_) {}
    activeAudio = null;
  }
  if (window.speechSynthesis) {
    window.speechSynthesis.cancel();
  }
  setAvatarSpeaking(false);
}

function setStatus(text, kind = "idle") {
  statusBarEl.textContent = text;
  statusBarEl.className = `status status--${kind}`;
}

function setBusy(isBusy) {
  state.isBusy = isBusy;
  queryInputEl.disabled = isBusy || !state.hasStarted;
  sendButtonEl.disabled = isBusy || !state.hasStarted;
  micButtonEl.disabled = isBusy || !state.hasStarted || !state.recognition;
}

function waitForRecognitionEnd() {
  if (!state.recognition || !state.isListening) {
    return Promise.resolve();
  }

  return new Promise((resolve) => {
    const recognition = state.recognition;
    const previousOnEnd = recognition.onend;
    recognition.onend = (event) => {
      state.isListening = false;
      if (typeof previousOnEnd === "function") {
        previousOnEnd(event);
      }
      recognition.onend = previousOnEnd;
      resolve();
    };
    try {
      recognition.stop();
    } catch (_) {
      state.isListening = false;
      recognition.onend = previousOnEnd;
      resolve();
    }
  });
}

function setAvatarSpeaking(isSpeaking) {
  if (!avatarEl) {
    return;
  }
  avatarEl.classList.toggle("is-speaking", isSpeaking);
}

function addMessage(role, text) {
  const wrapper = document.createElement("article");
  wrapper.className = `message message--${role}`;

  const label = document.createElement("div");
  label.className = "message__label";
  label.textContent = role === "assistant" ? "GHRU" : "You";

  const body = document.createElement("p");
  body.textContent = text;

  wrapper.append(label, body);
  transcriptEl.appendChild(wrapper);
  transcriptEl.scrollTop = transcriptEl.scrollHeight;
}

function resetConversation() {
  transcriptEl.innerHTML = "";
  state.language = "en";
  state.phase = "language";
  state.hasStarted = false;
  queryInputEl.value = "";
  assistantPaneEl.classList.add("assistant--hidden");
  shellEl.classList.remove("shell--started");
  startButtonEl.disabled = false;
  langSwapButtonEl.disabled = true;
  updateLangSwapButton();
  stopAllSpeech();
  setBusy(false);
  setStatus("Waiting to start", "idle");
}

async function requestJson(url, payload = null) {
  const options = payload
    ? {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      }
    : {};

  const response = await fetch(url, options);
  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`);
  }
  return response.json();
}

function getBrowserVoice() {
  const voices = window.speechSynthesis.getVoices();
  const preferredLang = state.language === "hi" ? "hi-IN" : "en-IN";
  let languageVoices = voices.filter((voice) => voice.lang === preferredLang);
  if (!languageVoices.length) {
    languageVoices = voices.filter((voice) => voice.lang.startsWith(state.language));
  }

  if (!languageVoices.length) {
    return null;
  }

  const femaleNameHints = [
    "female",
    "woman",
    "girl",
    "swara",
    "neerja",
    "priya",
    "aria",
    "sara",
    "heera",
    "sonia",
  ];
  return (
    languageVoices.find((voice) =>
      femaleNameHints.some((hint) => voice.name.toLowerCase().includes(hint))
    ) || null
  );
}

function speakFromServer(text) {
  return new Promise(async (resolve, reject) => {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), SERVER_TTS_TIMEOUT_MS);
    try {
      const response = await fetch("/api/tts", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text, language: state.language }),
        signal: controller.signal,
      });
      if (!response.ok) {
        reject(new Error(`TTS failed: ${response.status}`));
        return;
      }

      const blob = await response.blob();
      const objectUrl = URL.createObjectURL(blob);
      const audio = new Audio(objectUrl);
      audio.preload = "auto";
      audio.onplay = () => {
        setStatus("GHRU is speaking", "speaking");
        setAvatarSpeaking(true);
        activeAudio = audio;
      };
      audio.onended = () => {
        if (activeAudio === audio) activeAudio = null;
        setAvatarSpeaking(false);
        URL.revokeObjectURL(objectUrl);
        resolve();
      };
      audio.onerror = () => {
        if (activeAudio === audio) activeAudio = null;
        setAvatarSpeaking(false);
        URL.revokeObjectURL(objectUrl);
        reject(new Error("Audio playback failed"));
      };

      // Wait briefly for media readiness to avoid clipping the first spoken word.
      await new Promise((ready) => {
        let done = false;
        const finish = () => {
          if (done) return;
          done = true;
          ready();
        };
        audio.addEventListener("canplaythrough", finish, { once: true });
        setTimeout(finish, 250);
        audio.load();
      });
      await audio.play();
    } catch (error) {
      reject(error);
    } finally {
      clearTimeout(timeoutId);
    }
  });
}

function speakText(text) {
  return new Promise(async (resolve) => {
    if (!text || !text.trim()) {
      resolve(false);
      return;
    }
    try {
      await speakFromServer(text);
      resolve(true);
      return;
    } catch (_) {
      // Fallback to browser speech only if a female voice is available.
    }

    if (!("speechSynthesis" in window)) {
      resolve(false);
      return;
    }

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = state.language === "hi" ? "hi-IN" : "en-IN";
    utterance.rate = state.language === "hi" ? 0.95 : 1.0;
    utterance.pitch = state.language === "hi" ? 1.35 : 1.0;
    const voice = getBrowserVoice();
    if (!voice) {
      resolve(false);
      return;
    }
    utterance.voice = voice;

    utterance.onstart = () => {
      setStatus("GHRU is speaking", "speaking");
      setAvatarSpeaking(true);
    };
    utterance.onend = () => {
      setAvatarSpeaking(false);
      resolve(true);
    };
    utterance.onerror = () => {
      setAvatarSpeaking(false);
      resolve(false);
    };

    window.speechSynthesis.cancel();
    window.speechSynthesis.speak(utterance);
  });
}

async function speakThenShow(text, speakTextValue = null) {
  // Required process: wait 1 second, then start voice and text together.
  await new Promise((resolve) => window.setTimeout(resolve, 1000));
  const speechPromise = speakText(speakTextValue || text);
  addMessage("assistant", text);
  return await speechPromise;
}

function prewarmTts() {
  fetch("/api/tts", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text: "Ready.", language: state.language || "en" }),
  }).catch(() => {});
}

async function primeAudioOutput() {
  if (audioOutputPrimed) {
    return;
  }
  try {
    const AudioCtx = window.AudioContext || window.webkitAudioContext;
    if (!AudioCtx) {
      audioOutputPrimed = true;
      return;
    }
    const ctx = new AudioCtx();
    await ctx.resume();
    const oscillator = ctx.createOscillator();
    const gain = ctx.createGain();
    gain.gain.value = 0.00001;
    oscillator.connect(gain);
    gain.connect(ctx.destination);
    oscillator.start();
    oscillator.stop(ctx.currentTime + 0.08);
    await new Promise((resolve) => {
      oscillator.onended = resolve;
    });
    audioOutputPrimed = true;
    ctx.close();
  } catch (_) {
    // Ignore warmup failures and continue with normal playback.
  }
}

async function handleAssistantMessage(payload, autoListenAfter = false) {
  state.language = payload.language;
  state.phase = payload.phase;
  const assistantText = payload.message || payload.speak_message || "";
  const didSpeak = await speakThenShow(assistantText, assistantText);

  if (payload.ended) {
    setStatus("Conversation ended", "idle");
    setBusy(false);
    return;
  }

  if (autoListenAfter && state.recognition && didSpeak) {
    setBusy(false);
    startListening();
    return;
  }

  if (autoListenAfter && !didSpeak) {
    setStatus("Voice output failed. Tap Start Listening.", "idle");
    setBusy(false);
    queryInputEl.focus();
    return;
  }

  setStatus("Ready for your next question", "idle");
  setBusy(false);
  queryInputEl.focus();
}

async function submitQuery(rawQuery, source = "text") {
  const query = rawQuery.trim();
  const allowWhileBusy = source === "voice";
  if (!query || (state.isBusy && !allowWhileBusy)) {
    return;
  }

  setBusy(true);
  setStatus("Thinking...", "idle");
  addMessage("user", query);

  try {
    const payload = await requestJson("/api/respond", {
      query,
      language: state.language,
      phase: state.phase,
    });
    queryInputEl.value = "";
    await handleAssistantMessage(payload, true);
  } catch (_) {
    addMessage("assistant", "Something went wrong while contacting the assistant.");
    setStatus("Request failed", "idle");
    setBusy(false);
  }
}

function createRecognition() {
  const RecognitionClass =
    window.SpeechRecognition || window.webkitSpeechRecognition || null;
  if (!RecognitionClass) {
    return null;
  }

  const recognition = new RecognitionClass();
  recognition.lang = "en-IN";
  recognition.interimResults = false;
  recognition.maxAlternatives = 1;
  recognition.continuous = false;

  recognition.onstart = () => {
    state.isListening = true;
    setStatus("Listening...", "listening");
  };

  recognition.onresult = async (event) => {
    const transcript = event.results[0][0].transcript;
    await waitForRecognitionEnd();
    setBusy(false);
    await submitQuery(transcript, "voice");
  };

  recognition.onerror = () => {
    state.isListening = false;
    setStatus("Voice input failed. You can type instead.", "idle");
    setBusy(false);
  };

  recognition.onend = () => {
    state.isListening = false;
    if (!state.isBusy) {
      setStatus("Ready for your next question", "idle");
    }
  };

  return recognition;
}

function startListening() {
  if (!state.recognition || state.isBusy) {
    return;
  }

  setBusy(true);
  state.recognition.lang = state.language === "hi" ? "hi-IN" : "en-IN";
  try {
    state.recognition.start();
  } catch (_) {
    setBusy(false);
  }
}

function updateLangSwapButton() {
  // Reflect the current active language on the button
  if (state.language === "hi") {
    langSwapButtonEl.classList.add("lang-active-hi");
    langSwapButtonEl.title = "Switch to English";
  } else {
    langSwapButtonEl.classList.remove("lang-active-hi");
    langSwapButtonEl.title = "Switch to Hindi";
  }
}

async function swapLanguage() {
  if (!state.hasStarted) return;

  stopAllSpeech();

  // Flip the language
  const newLang = state.language === "en" ? "hi" : "en";
  state.language = newLang;
  state.phase = "chat"; // remain in chat — no need to re-select language

  // Update recognition language for next voice input
  if (state.recognition) {
    state.recognition.lang = newLang === "hi" ? "hi-IN" : "en-IN";
  }

  updateLangSwapButton();

  // Announcement in the newly selected language
  const announcement =
    newLang === "hi"
      ? "भाषा हिंदी में बदल दी गई है।"
      : "Language has been changed to English.";

  setBusy(true);
  setStatus("Switching language...", "idle");
  addMessage("assistant", announcement);
  await speakText(announcement);
  setBusy(false);
  setStatus("Ready for your next question", "idle");
  queryInputEl.focus();
}

async function startAssistant() {
  setBusy(true);
  setStatus("Starting assistant...", "idle");
  state.hasStarted = true;
  startButtonEl.disabled = true;
  shellEl.classList.add("shell--started");
  assistantPaneEl.classList.remove("assistant--hidden");
  queryInputEl.disabled = false;
  sendButtonEl.disabled = false;
  micButtonEl.disabled = !state.recognition;
  langSwapButtonEl.disabled = false;
  updateLangSwapButton();
  setBusy(false);
  queryInputEl.focus();

  // Do not block startup on warmup; run it in background.
  primeAudioOutput();

  try {
    const payload = await requestJson("/api/bootstrap");
    state.language = payload.language;
    state.phase = payload.phase;
    prewarmTts();
    await handleAssistantMessage(payload, true);
  } catch (_) {
    setStatus("Assistant could not start", "idle");
    setBusy(false);
  }
}

startButtonEl.addEventListener("click", async () => {
  await startAssistant();
});

micButtonEl.addEventListener("click", () => {
  startListening();
});

langSwapButtonEl.addEventListener("click", async () => {
  await swapLanguage();
});

exitButtonEl.addEventListener("click", async () => {
  await waitForRecognitionEnd();
  stopAllSpeech();
  resetConversation();
});

composerEl.addEventListener("submit", async (event) => {
  event.preventDefault();
  await submitQuery(queryInputEl.value, "text");
});

state.recognition = createRecognition();
if (!state.recognition) {
  micButtonEl.disabled = true;
  micButtonEl.textContent = "Voice Unsupported";
}

resetConversation();
