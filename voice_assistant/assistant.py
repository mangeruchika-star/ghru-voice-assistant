"""Core assistant logic."""

from __future__ import annotations

import asyncio
import datetime as dt
import html
import os
import re
import subprocess
import sys
import tempfile
import threading
import time
import wave
import winsound
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Callable



try:
    from .data import COLLEGE_INFO, COLLEGE_INFO_HI, RESPONSES
except ImportError:
    current_dir = Path(__file__).resolve().parent
    parent_dir = current_dir.parent
    if str(parent_dir) not in sys.path:
        sys.path.insert(0, str(parent_dir))
    from voice_assistant.data import COLLEGE_INFO, COLLEGE_INFO_HI, RESPONSES

try:
    import pyttsx3
except ImportError:  # pragma: no cover - environment dependent
    pyttsx3 = None

try:
    import speech_recognition as sr
except ImportError:  # pragma: no cover - environment dependent
    sr = None

try:
    import edge_tts
except ImportError:  # pragma: no cover - environment dependent
    edge_tts = None

try:
    from piper import PiperVoice
except ImportError:  # pragma: no cover - environment dependent
    PiperVoice = None

pygame = None


def _contains_any(text: str, keywords: tuple[str, ...]) -> bool:
    return any(keyword in text for keyword in keywords)


def _normalize_text(text: str) -> str:
    normalized = text.lower().strip()
    replacements = {
        ".": " ",
        ",": " ",
        "?": " ",
        "-": " ",
        "_": " ",
        "/": " ",
    }
    for old, new in replacements.items():
        normalized = normalized.replace(old, new)
    return " ".join(normalized.split())


def _strip_html_tags(text: str) -> str:
    no_tags = re.sub(r"<[^>]+>", " ", text)
    clean = html.unescape(no_tags)
    return " ".join(clean.split())


def _keyword_tokens(text: str) -> list[str]:
    stop_words = {
        "what",
        "when",
        "where",
        "which",
        "who",
        "how",
        "is",
        "are",
        "the",
        "a",
        "an",
        "for",
        "of",
        "in",
        "on",
        "to",
        "about",
        "tell",
        "me",
        "please",
        "details",
        "detail",
        "information",
        "info",
        "ghru",
        "college",
        "university",
        "cell",
        "anti",
    }
    tokens = re.findall(r"[a-zA-Z0-9]+", text.lower())
    return [tok for tok in tokens if len(tok) > 2 and tok not in stop_words]


@dataclass
class AssistantConfig:
    assistant_name: str
    language: str = "en"
    use_voice_input: bool = True
    show_assistant_text: bool = True


class CollegeVoiceAssistant:
    """Voice assistant with speech and keyboard fallbacks."""

    def __init__(self, config: AssistantConfig | None = None) -> None:
        language = (config.language if config else "en").lower()
        if language not in RESPONSES:
            language = "en"

        assistant_name = (
            config.assistant_name if config else RESPONSES[language]["assistant_name"]
        )
        self.config = AssistantConfig(
            assistant_name=assistant_name,
            language=language,
            use_voice_input=True if config is None else config.use_voice_input,
            show_assistant_text=True if config is None else config.show_assistant_text,
        )
        self.college_info = COLLEGE_INFO
        self.college_info_hi = COLLEGE_INFO_HI
        self.responses = RESPONSES
        self.project_root = Path(__file__).resolve().parent.parent
        self.voice_models_dir = self.project_root / "voice_models"
        self.engine = self._create_tts_engine()
        self.recognizer = sr.Recognizer() if sr and self.config.use_voice_input else None
        self.microphone_available = sr is not None and self.recognizer is not None
        self.microphone_index = self._select_microphone_index()
        self.warned_voice_fallback = False
        self._piper_voices: dict[str, PiperVoice] = {}

        self.query_aliases = {
            "c s e": "cse",
            "computer science engineering": "computer science",
            "computer science and engineering": "computer science",
            "b tech": "btech",
            "m tech": "mtech",
            "b sc": "bsc",
            "m sc": "msc",
            "b c a": "bca",
            "m c a": "mca",
            "m b a": "mba",
            "b b a": "bba",
            "e and tc": "electronics and telecommunication",
            "e tc": "electronics and telecommunication",
            "bus fee": "transport fee",
            "wi fi": "wifi",
            # Hindi intent aliases
            "फीस": "fees",
            "शुल्क": "fees",
            "कोर्स": "courses",
            "पाठ्यक्रम": "courses",
            "इंजीनियरिंग": "engineering",
            "अभियांत्रिकी": "engineering",
            "साइंस": "science",
            "विज्ञान": "science",
            "कॉमर्स": "commerce",
            "वाणिज्य": "commerce",
            "एडमिशन": "admission",
            "प्रवेश": "admission",
            "योग्यता": "eligibility",
            "सुविधा": "facilities",
            "सुविधाएं": "facilities",
            "सुविधाएँ": "facilities",
            "लाइब्रेरी": "library",
            "पुस्तकालय": "library",
            "हॉस्टल": "hostel",
            "होस्टल": "hostel",
            "परिवहन": "transport",
            "बस": "bus",
            "परीक्षा": "exam",
            "एग्जाम": "exam",
            "रिजल्ट": "result",
            "परिणाम": "result",
            "रीवैल्यूएशन": "revaluation",
            "पुनर्मूल्यांकन": "revaluation",
            "संपर्क": "contact",
            "ईमेल": "email",
            "वेबसाइट": "website",
            "लोकेशन": "location",
            "पता": "address",
            "ऑफिस": "office",
            "कार्यालय": "office",
            "समय": "time",
            "टाइमिंग": "timing",
            "कब खुलता": "open",
            "कब खुलती": "open",
            "डिप्लोमा": "diploma",
            "बीटेक": "btech",
            "एमटेक": "mtech",
            "बीएससी": "bsc",
            "एमएससी": "msc",
            "बीसीए": "bca",
            "एमसीए": "mca",
            "बीबीए": "bba",
            "एमबीए": "mba",
            "बायोलॉजी": "biology",
            "फिजिक्स": "physics",
            "केमिस्ट्री": "chemistry",
            "मैथमेटिक्स": "mathematics",
            "विद्युत": "electrical",
            "सिविल": "civil",
            "मैकेनिकल": "mechanical",
        }

    @property
    def language(self) -> str:
        return self.config.language

    @property
    def is_hindi(self) -> bool:
        return self.language == "hi"

    def _active_college_info(self) -> dict:
        return self.college_info_hi if self.is_hindi else self.college_info

    def _create_tts_engine(self):
        if pyttsx3 is None:
            return None

        try:
            engine = pyttsx3.init()
            voices = engine.getProperty("voices")
            if voices:
                female_hints = (
                    "female",
                    "woman",
                    "zira",
                    "hazel",
                    "heera",
                    "priya",
                    "swara",
                    "neerja",
                    "amy",
                    "susan",
                    "sara",
                )
                selected_voice = next(
                    (
                        voice
                        for voice in voices
                        if any(hint in voice.name.lower() for hint in female_hints)
                    ),
                    None,
                )
                if selected_voice is None:
                    return None
                engine.setProperty("voice", selected_voice.id)
            engine.setProperty("rate", 165)
            engine.setProperty("volume", 1.0)
            return engine
        except Exception:
            return None

    def _select_microphone_index(self) -> int | None:
        if sr is None or not self.config.use_voice_input:
            return None

        try:
            names = sr.Microphone.list_microphone_names()
        except Exception:
            return None

        strong_preferred_tokens = (
            "microphone array",
            "digital microphones",
            "realtek hd audio mic input",
            "microphone (",
        )
        preferred_tokens = ("microphone", "mic", "array", "input")
        blocked_tokens = ("output", "speaker", "stereo mix", "headphone")

        for index, raw_name in enumerate(names):
            name = raw_name.lower()
            if any(token in name for token in blocked_tokens):
                continue
            if any(token in name for token in strong_preferred_tokens):
                return index

        for index, raw_name in enumerate(names):
            name = raw_name.lower()
            if any(token in name for token in blocked_tokens):
                continue
            if "sound mapper" in name or "primary sound capture driver" in name:
                continue
            if any(token in name for token in preferred_tokens):
                return index

        for index, raw_name in enumerate(names):
            name = raw_name.lower()
            if any(token in name for token in blocked_tokens):
                continue
            if "sound mapper" in name or "primary sound capture driver" in name:
                return index
        return None

    def _speak_with_powershell(self, text: str) -> bool:
        return False

    async def _generate_edge_tts_audio(self, text: str, output_path: Path) -> None:
        voice = "en-IN-NeerjaNeural" if self.language == "en" else "hi-IN-SwaraNeural"
        communicator = edge_tts.Communicate(text, voice=voice)
        await communicator.save(str(output_path))

    def _prepare_edge_tts_audio(self, text: str) -> Path | None:
        if edge_tts is None:
            return None

        temp_path: Path | None = None
        for _ in range(3):
            try:
                with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_file:
                    temp_path = Path(temp_file.name)
                asyncio.run(self._generate_edge_tts_audio(text, temp_path))
                return temp_path
            except Exception:
                if temp_path and temp_path.exists():
                    try:
                        temp_path.unlink()
                    except OSError:
                        pass
                temp_path = None
                time.sleep(0.4)
        return None

    def _play_audio_file_windows(self, audio_path: Path) -> bool:
        if sys.platform != "win32":
            return False

        escaped_path = audio_path.resolve().as_uri().replace("'", "''")
        command = (
            "Add-Type -AssemblyName presentationCore; "
            "$player = New-Object System.Windows.Media.MediaPlayer; "
            f"$player.Open([Uri]'{escaped_path}'); "
            "Start-Sleep -Milliseconds 400; "
            "$player.Play(); "
            "while ($player.NaturalDuration.HasTimeSpan -eq $false) { Start-Sleep -Milliseconds 200 }; "
            "$duration = [Math]::Ceiling($player.NaturalDuration.TimeSpan.TotalMilliseconds); "
            "Start-Sleep -Milliseconds ($duration + 500); "
            "$player.Stop(); "
            "$player.Close()"
        )
        try:
            completed = subprocess.run(
                ["powershell", "-NoProfile", "-Command", command],
                check=False,
                capture_output=True,
                text=True,
            )
            return completed.returncode == 0
        except Exception:
            return False

    def _play_edge_tts_audio(self, audio_path: Path) -> bool:
        if not audio_path.exists():
            return False

        try:
            if self._play_audio_file_windows(audio_path):
                return True

            global pygame
            if pygame is None:
                os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
                try:
                    import pygame as pygame_module
                except ImportError:
                    return False
                pygame = pygame_module

            if pygame is None:
                return False

            pygame.mixer.init()
            pygame.mixer.music.load(str(audio_path))
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                time.sleep(0.1)
            pygame.mixer.music.unload()
            pygame.mixer.quit()
            return True
        except Exception:
            try:
                if pygame and pygame.mixer.get_init():
                    pygame.mixer.music.stop()
                    pygame.mixer.quit()
            except Exception:
                pass
            return False

    def _display_text_response(self, text: str) -> None:
        print(f"{self.config.assistant_name}: {text}")

    def _get_piper_model_path(self) -> Path | None:
        if self.language == "hi":
            model_name = "hi_IN-pratham-medium.onnx"
        else:
            model_name = "en_US-amy-medium.onnx"

        model_path = self.voice_models_dir / model_name
        return model_path if model_path.exists() else None

    def _get_piper_voice(self) -> PiperVoice | None:
        if PiperVoice is None:
            return None

        model_path = self._get_piper_model_path()
        if model_path is None:
            return None

        cache_key = str(model_path)
        cached_voice = self._piper_voices.get(cache_key)
        if cached_voice is not None:
            return cached_voice

        try:
            voice = PiperVoice.load(model_path)
        except Exception:
            return None

        self._piper_voices[cache_key] = voice
        return voice

    def _speak_with_piper(self, text: str) -> bool:
        voice = self._get_piper_voice()
        if voice is None:
            return False

        temp_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                temp_path = Path(temp_file.name)

            with wave.open(str(temp_path), "wb") as wav_file:
                voice.synthesize_wav(text, wav_file)

            winsound.PlaySound(str(temp_path), winsound.SND_FILENAME)
            return True
        except Exception:
            return False
        finally:
            if temp_path and temp_path.exists():
                try:
                    temp_path.unlink()
                except OSError:
                    pass

    def _speak_now(self, text: str) -> None:
        clean_text = " ".join(text.split())
        # In Hindi mode, prefer Edge TTS first to keep voice output female (hi-IN-SwaraNeural).
        if self.is_hindi:
            edge_audio_path = self._prepare_edge_tts_audio(clean_text)
            if edge_audio_path is not None:
                try:
                    if self._play_edge_tts_audio(edge_audio_path):
                        return
                finally:
                    if edge_audio_path.exists():
                        try:
                            edge_audio_path.unlink()
                        except OSError:
                            pass
            if self._speak_with_piper(clean_text):
                return
        else:
            if self._speak_with_piper(clean_text):
                return
            edge_audio_path = self._prepare_edge_tts_audio(clean_text)
            if edge_audio_path is not None:
                try:
                    if self._play_edge_tts_audio(edge_audio_path):
                        return
                finally:
                    if edge_audio_path.exists():
                        try:
                            edge_audio_path.unlink()
                        except OSError:
                            pass

        if self.engine:
            try:
                self.engine.say(clean_text)
                self.engine.runAndWait()
                return
            except Exception:
                self.engine = None
        if self.engine is None and self._speak_with_powershell(clean_text):
            return

        if not self.warned_voice_fallback:
            self.warned_voice_fallback = True
            warning = (
                "Voice output is not available on this system, so I will keep showing responses in writing."
            )
            if self.config.show_assistant_text:
                self._display_text_response(warning)

    def speak(self, text: str) -> None:
        clean_text = " ".join(text.split())
        playback_thread = threading.Thread(
            target=self._speak_now,
            args=(clean_text,),
            daemon=True,
        )
        playback_thread.start()
        if self.config.show_assistant_text:
            time.sleep(1.0)
            self._display_text_response(clean_text)
        playback_thread.join()

    def listen(self) -> str:
        if self.microphone_available:
            try:
                with sr.Microphone(device_index=self.microphone_index) as source:
                    if self.config.show_assistant_text:
                        print(f"Listening (Mic ID: {self.microphone_index if self.microphone_index is not None else 'Default'})...")
                    
                    self.recognizer.adjust_for_ambient_noise(source, duration=0.6)
                    try:
                        audio = self.recognizer.listen(source, timeout=8, phrase_time_limit=12)
                    except sr.WaitTimeoutError:
                        return ""
                    except Exception as e:
                        if self.config.show_assistant_text:
                            print(f"Mic error: {e}")
                        raise e
            except Exception:
                self.microphone_available = False
                self.speak(self.responses[self.language]["input_fallback"])
                return input("You: ").strip().lower()

            try:
                text = self.recognizer.recognize_google(audio)
                if self.config.show_assistant_text:
                    print(f"You: {text}")
                return self.normalize_query(text)
            except sr.UnknownValueError:
                return ""
            except sr.RequestError:
                self.speak(self.responses[self.language]["recognition_unavailable"])
                return self.normalize_query(input("You: "))

        return self.normalize_query(input("You: "))

    def normalize_query(self, query: str) -> str:
        normalized = _normalize_text(query)
        for source, target in self.query_aliases.items():
            normalized = normalized.replace(source, target)
        return " ".join(normalized.split())

    def choose_language(self) -> None:
        self.speak("Choose language. Say or type English or Hindi.")
        selection = self.listen()
        if (
            "hindi" in selection
            or "हिंदी" in selection
            or "हिन्दी" in selection
            or selection.strip() == "hi"
        ):
            self.config.language = "hi"
        else:
            self.config.language = "en"
        self.speak(self.responses[self.language]["language_selected"])

    def build_help(self) -> str:
        return self.responses[self.language]["help"]

    def build_college_overview(self) -> str:
        info = self._active_college_info()
        if self.is_hindi:
            return (
                f"{info['name']} का location {info['location']} है। "
                f"Official website {info['website']} है और main email {info['email']} है।"
            )
        return (
            f"{info['name']} is located at {info['location']}. "
            f"The official website is {info['website']} and the main email is "
            f"{info['email']}."
        )

    def build_location_summary(self) -> str:
        info = self._active_college_info()
        if self.is_hindi:
            return f"{info['name']} का location {info['location']} है।"
        return (
            f"{info['name']} is located at {info['location']}."
        )

    def build_general_contact_summary(self) -> str:
        info = self._active_college_info()
        departments = info["departments"]
        if self.is_hindi:
            return (
                f"Main email {info['email']} है। Website {info['website']} है। "
                f"Admission contact: {departments['admission']}। Examination contact: {departments['examination']}। "
                f"Library contact: {departments['library']}। Hostel contact: {departments['hostel']}।"
            )
        return (
            f"Main email is {info['email']}. Website is {info['website']}. "
            f"Admission contact: {departments['admission']}. Examination contact: {departments['examination']}. "
            f"Library contact: {departments['library']}. Hostel contact: {departments['hostel']}."
        )

    def build_specific_department_contact(self, query: str) -> str:
        departments = self._active_college_info()["departments"]
        if _contains_any(query, ("admission", "apply")):
            if self.is_hindi:
                return f"एडमिशन विभाग का ईमेल {departments['admission']} है।"
            return f"Admission department email is {departments['admission']}."
        if _contains_any(query, ("exam", "examination", "result", "revaluation")):
            if self.is_hindi:
                return f"परीक्षा विभाग का ईमेल {departments['examination']} है।"
            return f"Examination department email is {departments['examination']}."
        if _contains_any(query, ("library", "books")):
            if self.is_hindi:
                return f"लाइब्रेरी विभाग का ईमेल {departments['library']} है।"
            return f"Library department email is {departments['library']}."
        if _contains_any(query, ("hostel", "accommodation")):
            if self.is_hindi:
                return f"हॉस्टल विभाग का ईमेल {departments['hostel']} है।"
            return f"Hostel department email is {departments['hostel']}."
        return self.build_general_contact_summary()

    def build_course_summary(self) -> str:
        courses = self._active_college_info()["courses"]
        if self.is_hindi:
            return (
                "इंजीनियरिंग में बी.टेक के लिए उपलब्ध कोर्स हैं "
                + ", ".join(courses["engineering"]["btech"])
                + "। साइंस में बी.एससी के कोर्स हैं "
                + ", ".join(courses["science"]["bsc"])
                + "। कॉमर्स में बीबीए और एमबीए स्पेशलाइजेशन उपलब्ध हैं। डिप्लोमा कोर्स उपलब्ध हैं "
                + ", ".join(courses["diploma"]["courses"])
                + "।"
            )
        return (
            "Engineering offers B.Tech in "
            + ", ".join(courses["engineering"]["btech"])
            + ". Science offers B.Sc in "
            + ", ".join(courses["science"]["bsc"])
            + ". Commerce offers BBA and MBA specializations. Diploma programs are available in "
            + ", ".join(courses["diploma"]["courses"])
            + "."
        )

    def build_specific_course_summary(self, query: str) -> str:
        courses = self._active_college_info()["courses"]

        if _contains_any(query, ("btech", "b.tech")):
            eng_btech = ", ".join(courses["engineering"]["btech"])
            if self.is_hindi:
                return "बी.टेक के कोर्स हैं " + eng_btech + "।"
            return "B.Tech courses are " + eng_btech + "."
        if _contains_any(query, ("mtech", "m.tech")):
            eng_mtech = ", ".join(courses["engineering"]["mtech"])
            if self.is_hindi:
                return "एम.टेक के कोर्स हैं " + eng_mtech + "।"
            return "M.Tech courses are " + eng_mtech + "."
        if _contains_any(query, ("engineering",)):
            eng_btech = ", ".join(courses["engineering"]["btech"])
            eng_mtech = ", ".join(courses["engineering"]["mtech"])
            if self.is_hindi:
                return (
                    "इंजीनियरिंग में बी.टेक के कोर्स हैं "
                    + eng_btech
                    + "। एम.टेक के कोर्स हैं "
                    + eng_mtech
                    + "।"
                )
            return (
                "Engineering offers B.Tech in "
                + eng_btech
                + ". M.Tech offers "
                + eng_mtech
                + "."
            )
        if _contains_any(query, ("bsc", "b.sc")):
            science_bsc = ", ".join(courses["science"]["bsc"])
            if self.is_hindi:
                return "बीएससी के कोर्स हैं " + science_bsc + "।"
            return "B.Sc courses are " + science_bsc + "."
        if _contains_any(query, ("msc", "m.sc")):
            science_msc = ", ".join(courses["science"]["msc"])
            if self.is_hindi:
                return "एमएससी के कोर्स हैं " + science_msc + "।"
            return "M.Sc courses are " + science_msc + "."
        if _contains_any(query, ("bca",)):
            if self.is_hindi:
                return "बीसीए कोर्स उपलब्ध है।"
            return "BCA is available."
        if _contains_any(query, ("mca",)):
            if self.is_hindi:
                return "एमसीए कोर्स उपलब्ध है।"
            return "MCA is available."
        if _contains_any(query, ("science",)):
            science_bsc = ", ".join(courses["science"]["bsc"])
            science_msc = ", ".join(courses["science"]["msc"])
            if self.is_hindi:
                return (
                    "साइंस में बीएससी के कोर्स हैं "
                    + science_bsc
                    + "। एमएससी के कोर्स हैं "
                    + science_msc
                    + "।"
                )
            return (
                "Science offers B.Sc in "
                + science_bsc
                + ". M.Sc offers "
                + science_msc
                + "."
            )
        if _contains_any(query, ("diploma", "computer engineering", "electronics engineering")):
            diploma_courses = ", ".join(courses["diploma"]["courses"])
            if self.is_hindi:
                return "डिप्लोमा में उपलब्ध कोर्स हैं " + diploma_courses + "।"
            return "Diploma programs are available in " + diploma_courses + "."
        if _contains_any(query, ("commerce", "bba", "mba")):
            if self.is_hindi:
                return "कॉमर्स में BBA और MBA कोर्स उपलब्ध हैं।"
            return "Commerce offers BBA and MBA programs."

        if _contains_any(query, ("computer science", "cse")):
            if self.is_hindi:
                return "बी.टेक कंप्यूटर साइंस एंड इंजीनियरिंग उपलब्ध है।"
            return "B.Tech Computer Science and Engineering is available."
        if _contains_any(query, ("mechanical",)):
            if self.is_hindi:
                return "मैकेनिकल इंजीनियरिंग बी.टेक में उपलब्ध है।"
            return "Mechanical Engineering is available in B.Tech."
        if _contains_any(query, ("electrical",)):
            if self.is_hindi:
                return "इलेक्ट्रिकल इंजीनियरिंग बी.टेक में उपलब्ध है।"
            return "Electrical Engineering is available in B.Tech."
        if _contains_any(query, ("civil",)):
            if self.is_hindi:
                return "सिविल इंजीनियरिंग बी.टेक में उपलब्ध है।"
            return "Civil Engineering is available in B.Tech."
        if _contains_any(query, ("electronics and telecommunication", "telecommunication", "etc")):
            if self.is_hindi:
                return "इलेक्ट्रॉनिक्स एंड टेलीकम्युनिकेशन बी.टेक में उपलब्ध है।"
            return "Electronics and Telecommunication is available in B.Tech."
        if _contains_any(query, ("information technology", "it")):
            if self.is_hindi:
                return "इन्फॉर्मेशन टेक्नोलॉजी बी.टेक में उपलब्ध है।"
            return "Information Technology is available in B.Tech."
        if _contains_any(query, ("vlsi",)):
            if self.is_hindi:
                return "वीएलएसआई डिजाइन एम.टेक में उपलब्ध है।"
            return "VLSI Design is available in M.Tech."
        if _contains_any(query, ("power systems",)):
            if self.is_hindi:
                return "पावर सिस्टम्स एम.टेक में उपलब्ध है।"
            return "Power Systems is available in M.Tech."
        if _contains_any(query, ("structural",)):
            if self.is_hindi:
                return "स्ट्रक्चरल इंजीनियरिंग एम.टेक में उपलब्ध है।"
            return "Structural Engineering is available in M.Tech."
        if _contains_any(query, ("physics",)):
            if self.is_hindi:
                return "फिजिक्स बी.एससी और एम.एससी में उपलब्ध है।"
            return "Physics is available in B.Sc and M.Sc."
        if _contains_any(query, ("chemistry", "organic chemistry")):
            if self.is_hindi:
                return "केमिस्ट्री बी.एससी और एम.एससी में उपलब्ध है, और ऑर्गेनिक केमिस्ट्री एम.एससी में उपलब्ध है।"
            return "Chemistry is available in B.Sc and M.Sc, and Organic Chemistry is available in M.Sc."
        if _contains_any(query, ("mathematics", "maths", "math")):
            if self.is_hindi:
                return "मैथमेटिक्स बी.एससी और एम.एससी में उपलब्ध है।"
            return "Mathematics is available in B.Sc and M.Sc."
        if _contains_any(query, ("biology",)):
            if self.is_hindi:
                return "बायोलॉजी बी.एससी में उपलब्ध है।"
            return "Biology is available in B.Sc."
        if _contains_any(query, ("accounting", "finance", "marketing", "business management")):
            if self.is_hindi:
                return "ये स्पेशलाइजेशन बीबीए या एमबीए में उपलब्ध हैं।"
            return "These specializations are available in BBA or MBA."

        return self.build_course_summary()

    def build_fee_summary(self) -> str:
        fees = self._active_college_info()["fees"]
        if self.is_hindi:
            return (
                f"बी.टेक और एम.टेक इंजीनियरिंग की फीस {fees['engineering']} है, साइंस फीस {fees['science']} है, "
                f"बीसीए फीस {fees['bca']} है, एमसीए फीस {fees['mca']} है, "
                f"कॉमर्स फीस {fees['commerce']} है, डिप्लोमा फीस {fees['diploma']} है, "
                f"हॉस्टल फीस {fees['hostel']} है, और ट्रांसपोर्ट फीस {fees['transport']} है।"
            )
        return (
            f"B.Tech and M.Tech engineering fee is {fees['engineering']}, science fee is {fees['science']}, "
            f"BCA fee is {fees['bca']}, MCA fee is {fees['mca']}, "
            f"commerce fee is {fees['commerce']}, diploma fee is {fees['diploma']}, "
            f"hostel fee is {fees['hostel']}, and transport fee is {fees['transport']}."
        )

    def build_specific_fee_summary(self, query: str) -> str:
        fees = self._active_college_info()["fees"]

        if _contains_any(
            query,
            (
                "btech cse",
                "computer science",
                "cse",
                "btech computer science",
            ),
        ):
            if self.is_hindi:
                return f"बी.टेक कंप्यूटर साइंस एंड इंजीनियरिंग की फीस {fees['engineering']} है।"
            return (
                f"The fee for B.Tech Computer Science and Engineering is {fees['engineering']}."
            )
        if _contains_any(query, ("mechanical", "electrical", "civil", "information technology")):
            if self.is_hindi:
                return f"इस बी.टेक इंजीनियरिंग कोर्स की फीस {fees['btech']} है।"
            return f"The fee for this B.Tech engineering course is {fees['btech']}."
        if _contains_any(query, ("electronics and telecommunication", "telecommunication", "etc")):
            if self.is_hindi:
                return f"बी.टेक इलेक्ट्रॉनिक्स एंड टेलीकम्युनिकेशन की फीस {fees['btech']} है।"
            return (
                "The fee for B.Tech Electronics and Telecommunication is "
                f"{fees['btech']}."
            )
        if _contains_any(query, ("btech", "b.tech")):
            if self.is_hindi:
                return f"बी.टेक की फीस {fees['btech']} है।"
            return f"The fee for B.Tech is {fees['btech']}."
        if _contains_any(query, ("mtech vlsi", "vlsi")):
            if self.is_hindi:
                return f"एम.टेक वीएलएसआई डिजाइन की फीस {fees['mtech']} है।"
            return f"The fee for M.Tech VLSI Design is {fees['mtech']}."
        if _contains_any(query, ("mtech power systems", "power systems")):
            if self.is_hindi:
                return f"एम.टेक पावर सिस्टम्स की फीस {fees['mtech']} है।"
            return f"The fee for M.Tech Power Systems is {fees['mtech']}."
        if _contains_any(query, ("mtech structural", "structural engineering", "structural")):
            if self.is_hindi:
                return f"एम.टेक स्ट्रक्चरल इंजीनियरिंग की फीस {fees['mtech']} है।"
            return f"The fee for M.Tech Structural Engineering is {fees['mtech']}."
        if _contains_any(query, ("mtech", "m.tech")):
            if self.is_hindi:
                return f"एम.टेक की फीस {fees['mtech']} है।"
            return f"The fee for M.Tech is {fees['mtech']}."

        if _contains_any(query, ("btech", "b.tech", "mtech", "m.tech", "engineering")):
            if self.is_hindi:
                return (
                    f"बी.टेक की फीस {fees['btech']} है और एम.टेक की फीस {fees['mtech']} है। "
                    "यह फीस इंजीनियरिंग ब्रांचेस के लिए लागू है।"
                )
            return (
                f"The fee for B.Tech is {fees['btech']} and the fee for M.Tech is {fees['mtech']}. "
                "These fees apply to the engineering branches."
            )

        if _contains_any(query, ("physics", "chemistry", "mathematics", "biology", "computer science")):
            if self.is_hindi:
                return f"इस साइंस कोर्स की फीस {fees['science']} है।"
            return f"The fee for this science course is {fees['science']}."
        if _contains_any(query, ("msc", "m.sc")):
            science_fees = self._active_college_info()["courses"]["science"]
            msc_fee = science_fees.get("fees_postgraduate", fees["science"])
            if self.is_hindi:
                return f"एमएससी की फीस {msc_fee} है।"
            return f"The fee for M.Sc is {msc_fee}."
        if _contains_any(query, ("bsc", "b.sc")):
            if self.is_hindi:
                return f"बीएससी की फीस {fees['science']} है।"
            return f"The fee for B.Sc is {fees['science']}."
        if _contains_any(query, ("bca",)):
            if self.is_hindi:
                return f"बीसीए की फीस {fees['bca']} है।"
            return f"The fee for BCA is {fees['bca']}."
        if _contains_any(query, ("mca",)):
            if self.is_hindi:
                return f"एमसीए की फीस {fees['mca']} है।"
            return f"The fee for MCA is {fees['mca']}."
        if _contains_any(query, ("science",)):
            if self.is_hindi:
                return f"साइंस कोर्स की फीस {fees['science']} है।"
            return f"The fee for science courses is {fees['science']}."

        if _contains_any(query, ("mba",)):
            if self.is_hindi:
                return f"एमबीए की फीस {fees['commerce']} है।"
            return f"The fee for MBA is {fees['commerce']}."
        if _contains_any(query, ("bba",)):
            if self.is_hindi:
                return f"बीबीए की फीस {fees['commerce']} है।"
            return f"The fee for BBA is {fees['commerce']}."
        if _contains_any(query, ("accounting", "finance", "marketing", "business management")):
            if self.is_hindi:
                return f"इस कॉमर्स कोर्स की फीस {fees['commerce']} है।"
            return f"The fee for this commerce course is {fees['commerce']}."
        if _contains_any(query, ("bba", "mba", "commerce")):
            if self.is_hindi:
                return f"कॉमर्स कोर्स की फीस {fees['commerce']} है।"
            return f"The fee for commerce courses is {fees['commerce']}."

        if _contains_any(query, ("computer engineering", "electronics engineering")):
            if self.is_hindi:
                return f"इस डिप्लोमा कोर्स की फीस {fees['diploma']} है।"
            return f"The fee for this diploma course is {fees['diploma']}."
        if _contains_any(query, ("diploma",)):
            if self.is_hindi:
                return f"डिप्लोमा कोर्स की फीस {fees['diploma']} है।"
            return f"The fee for diploma courses is {fees['diploma']}."

        if _contains_any(query, ("hostel with mess",)):
            if self.is_hindi:
                return f"मेस सहित हॉस्टल फीस {fees['hostel']} है।"
            return f"The hostel fee with mess is {fees['hostel']}."
        if _contains_any(query, ("hostel", "mess")):
            if self.is_hindi:
                return f"हॉस्टल फीस {fees['hostel']} है।"
            return f"The hostel fee is {fees['hostel']}."

        if _contains_any(query, ("transport", "bus")):
            if self.is_hindi:
                return f"ट्रांसपोर्ट फीस {fees['transport']} है।"
            return f"The transport fee is {fees['transport']}."

        return self.build_fee_summary()

    def build_admission_summary(self) -> str:
        admission = self._active_college_info()["admission"]
        if self.is_hindi:
            return (
                f"एडमिशन प्रक्रिया में {admission['process']} शामिल है। "
                f"प्रवेश परीक्षा: {admission['entrance_exam']}। "
                f"योग्यता: {admission['eligibility']}।"
            )
        return (
            f"Admission process includes {admission['process']}. "
            f"Entrance exam: {admission['entrance_exam']}. "
            f"Eligibility: {admission['eligibility']}."
        )

    def build_facilities_summary(self) -> str:
        facilities = self._active_college_info()["facilities"]
        if self.is_hindi:
            return (
                f"सुविधाओं में {facilities['library']} शामिल है, लैब जैसे "
                f"{', '.join(facilities['laboratories'])}, खेल सुविधाएं जैसे "
                f"{', '.join(facilities['sports'])}, हॉस्टल सुविधा, ट्रांसपोर्ट, मेडिकल सहायता "
                f"और {facilities['wifi']} उपलब्ध है।"
            )
        return (
            f"Facilities include {facilities['library']}, labs such as "
            f"{', '.join(facilities['laboratories'])}, sports areas like "
            f"{', '.join(facilities['sports'])}, hostel support, transport, medical help, "
            f"and {facilities['wifi']}."
        )

    def build_specific_facility_summary(self, query: str) -> str:
        info = self._active_college_info()
        facilities = info["facilities"]
        if _contains_any(query, ("library", "books")):
            if self.is_hindi:
                return (
                    f"{facilities['library']}। लाइब्रेरी टाइमिंग {info['library_timing']} है।"
                )
            return (
                f"{facilities['library']}. Library timing is {info['library_timing']}."
            )
        if _contains_any(query, ("lab", "labs", "laboratory", "laboratories")):
            if self.is_hindi:
                return "उपलब्ध लैब हैं: " + ", ".join(facilities["laboratories"]) + "।"
            return "Laboratories available are: " + ", ".join(facilities["laboratories"]) + "."
        if _contains_any(query, ("sports", "ground", "stadium", "gym")):
            if self.is_hindi:
                return "खेल सुविधाएं हैं: " + ", ".join(facilities["sports"]) + "।"
            return "Sports facilities include: " + ", ".join(facilities["sports"]) + "."
        if _contains_any(query, ("hostel", "accommodation", "mess")):
            if self.is_hindi:
                return (
                    f"{facilities['hostel']}। हॉस्टल फीस {info['fees']['hostel']} है।"
                )
            return (
                f"{facilities['hostel']}. Hostel fee is {info['fees']['hostel']}."
            )
        if _contains_any(query, ("transport", "bus", "travel")):
            if self.is_hindi:
                return (
                    f"{facilities['transport']}। ट्रांसपोर्ट फीस {info['fees']['transport']} है।"
                )
            return (
                f"{facilities['transport']}. Transport fee is {info['fees']['transport']}."
            )
        if _contains_any(query, ("medical", "doctor", "health", "ambulance")):
            if self.is_hindi:
                return facilities["medical"] + "।"
            return facilities["medical"] + "."
        if _contains_any(query, ("wifi", "internet")):
            if self.is_hindi:
                return facilities["wifi"] + "।"
            return facilities["wifi"] + "."
        return self.build_facilities_summary()

    def build_exam_summary(self) -> str:
        exams = self._active_college_info()["exams"]
        if self.is_hindi:
            return (
                f"{exams['internal']}। {exams['external']}। {exams['result']}। "
                f"{exams['revaluation']}।"
            )
        return (
            f"{exams['internal']}. {exams['external']}. {exams['result']}. "
            f"{exams['revaluation']}."
        )

    def build_specific_exam_summary(self, query: str) -> str:
        exams = self._active_college_info()["exams"]
        if _contains_any(query, ("internal", "mid sem", "midterm")):
            return exams["internal"] + ("।" if self.is_hindi else ".")
        if _contains_any(query, ("external", "semester", "university exam")):
            return exams["external"] + ("।" if self.is_hindi else ".")
        if _contains_any(query, ("result", "results")):
            return exams["result"] + ("।" if self.is_hindi else ".")
        if _contains_any(query, ("revaluation", "recheck", "re-total", "re total")):
            return exams["revaluation"] + ("।" if self.is_hindi else ".")
        return self.build_exam_summary()

    def build_department_summary(self) -> str:
        departments = self._active_college_info()["departments"]
        if self.is_hindi:
            return (
                f"एडमिशन: {departments['admission']}। परीक्षा: {departments['examination']}। "
                f"लाइब्रेरी: {departments['library']}। हॉस्टल: {departments['hostel']}।"
            )
        return (
            f"Admission: {departments['admission']}. Examination: {departments['examination']}. "
            f"Library: {departments['library']}. Hostel: {departments['hostel']}."
        )

    def build_timing_summary(self) -> str:
        info = self._active_college_info()
        if self.is_hindi:
            return (
                f"ऑफिस टाइमिंग {info['office_timing']} है। "
                f"लाइब्रेरी टाइमिंग {info['library_timing']} है।"
            )
        return (
            f"Office timing is {info['office_timing']}. "
            f"Library timing is {info['library_timing']}."
        )

    def build_datetime_summary(self) -> str:
        now = dt.datetime.now()
        if self.is_hindi:
            return now.strftime("आज की तारीख %d %B %Y है और समय %I:%M %p है।")
        return now.strftime("Current date is %d %B %Y and the time is %I:%M %p.")

    @staticmethod
    @lru_cache(maxsize=64)
    def _lookup_from_official_site(raw_query: str) -> str | None:
        query = raw_query.strip()
        if not query:
            return None
        query_tokens = _keyword_tokens(query)
        if not query_tokens:
            return None

        sitemap_url = "https://ghru.edu.in/sitemap.xml"
        try:
            with urlopen(sitemap_url, timeout=2) as response:
                sitemap_xml = response.read().decode("utf-8", errors="ignore")
        except (URLError, TimeoutError, ValueError):
            return None

        urls = re.findall(r"<loc>(https?://[^<]+)</loc>", sitemap_xml, flags=re.IGNORECASE)
        if not urls:
            return None

        direct_topic_pages = {
            "placement": "https://ghru.edu.in/training-placement",
            "placements": "https://ghru.edu.in/training-placement",
            "scholarship": "https://ghru.edu.in/student-scholarship",
            "scholarships": "https://ghru.edu.in/student-scholarship",
        }

        for token in query_tokens:
            direct_url = direct_topic_pages.get(token)
            if direct_url and direct_url in urls:
                candidates = [direct_url]
                break
        else:
            candidates = []

        def url_score(candidate_url: str) -> int:
            path_text = candidate_url.lower().replace("-", " ").replace("/", " ")
            return sum(1 for tok in query_tokens if tok in path_text)

        if not candidates:
            ranked_urls = sorted(urls, key=url_score, reverse=True)
            candidates = [u for u in ranked_urls if url_score(u) > 0][:3]
            if not candidates:
                return None

        best_result: tuple[int, str, str, str] | None = None
        for candidate_url in candidates:
            try:
                with urlopen(candidate_url, timeout=2) as response:
                    candidate_html = response.read().decode("utf-8", errors="ignore")
            except (URLError, TimeoutError, ValueError):
                continue

            title_match = re.search(r"<title>(.*?)</title>", candidate_html, flags=re.IGNORECASE | re.DOTALL)
            title = _strip_html_tags(title_match.group(1)) if title_match else "GHRU"

            paragraph_match = re.search(r"<p[^>]*>(.*?)</p>", candidate_html, flags=re.IGNORECASE | re.DOTALL)
            snippet = _strip_html_tags(paragraph_match.group(1)) if paragraph_match else ""
            snippet = snippet[:320].rstrip()

            lowered_url = candidate_url.lower().replace("-", " ")
            lowered_title = title.lower()
            title_hits = sum(1 for tok in query_tokens if tok in lowered_title)
            url_hits = sum(1 for tok in query_tokens if tok in lowered_url)
            score = (title_hits * 3) + (url_hits * 2)
            if best_result is None or score > best_result[0]:
                best_result = (score, candidate_url, title, snippet)

        if best_result is None or best_result[0] <= 0:
            return None

        _, result_url, result_title, snippet = best_result

        if snippet:
            return (
                f"I found this on the official GHRU website: {result_title}. "
                f"{snippet}. You can read more at {result_url}."
            )

        return (
            f"I found this on the official GHRU website: {result_title}. "
            f"You can read more at {result_url}."
        )

    def handle_query(self, query: str) -> str:
        query = self.normalize_query(query)
        if not query:
            return self.responses[self.language]["not_understood"]

        course_keywords = (
            "course",
            "courses",
            "btech",
            "mtech",
            "bsc",
            "msc",
            "bca",
            "mca",
            "mba",
            "bba",
            "diploma",
            "computer science",
            "cse",
            "mechanical",
            "electrical",
            "civil",
            "electronics and telecommunication",
            "information technology",
            "vlsi",
            "power systems",
            "structural",
            "physics",
            "chemistry",
            "mathematics",
            "biology",
            "accounting",
            "finance",
            "marketing",
            "business management",
        )
        location_keywords = (
            "location",
            "address",
            "where is",
            "where located",
            "where are you",
            "college address",
        )
        contact_keywords = (
            "contact",
            "phone",
            "email",
            "mail",
            "website",
            "site",
            "department contact",
        )
        facility_keywords = (
            "facility",
            "facilities",
            "hostel",
            "lab",
            "labs",
            "sports",
            "wifi",
            "library",
            "medical",
            "transport",
            "bus",
            "accommodation",
            "internet",
        )
        exam_keywords = (
            "exam",
            "exams",
            "result",
            "revaluation",
            "internal",
            "external",
            "semester",
            "mid sem",
            "midterm",
        )
        timing_keywords = (
            "timing",
            "timings",
            "office time",
            "library time",
            "open",
            "hours",
            "working hours",
            "when open",
            "what time",
        )

        handlers: list[tuple[Callable[[str], bool], Callable[[], str]]] = [
            (lambda text: _contains_any(text, ("help", "menu", "options")), self.build_help),
            (
                lambda text: _contains_any(text, location_keywords),
                self.build_location_summary,
            ),
            (
                lambda text: _contains_any(text, ("department",)),
                self.build_department_summary,
            ),
            (
                lambda text: _contains_any(text, contact_keywords),
                lambda: self.build_specific_department_contact(query),
            ),
            (
                lambda text: _contains_any(text, ("about", "university", "overview", "about college", "college info")),
                self.build_college_overview,
            ),
            (
                lambda text: _contains_any(text, ("fee", "fees", "hostel fee", "transport fee")),
                lambda: self.build_specific_fee_summary(query),
            ),
            (
                lambda text: _contains_any(text, course_keywords)
                or ("available" in text and _contains_any(text, course_keywords)),
                lambda: self.build_specific_course_summary(query),
            ),
            (
                lambda text: _contains_any(text, ("admission", "apply", "eligibility", "entrance")),
                self.build_admission_summary,
            ),
            (
                lambda text: _contains_any(text, timing_keywords),
                self.build_timing_summary,
            ),
            (
                lambda text: _contains_any(text, exam_keywords),
                lambda: self.build_specific_exam_summary(query),
            ),
            (
                lambda text: _contains_any(text, facility_keywords),
                lambda: self.build_specific_facility_summary(query),
            ),
            (
                lambda text: _contains_any(text, ("time", "date", "today")),
                self.build_datetime_summary,
            ),
        ]

        for matcher, builder in handlers:
            if matcher(query):
                return builder()

        site_answer = self._lookup_from_official_site(query)
        if site_answer:
            return site_answer

        return (
            self.responses[self.language]["not_understood"]
            + (
                " मुझे आधिकारिक GHRU वेबसाइट पर स्पष्ट रूप से मिलती-जुलती जानकारी नहीं मिली। "
                if self.is_hindi
                else " I could not find a clearly matching answer on the official GHRU website. "
            )
            + self.build_help()
        )

    def run(self) -> int:
        self.speak("Hello, I am GHRU, your college voice assistant.")
        self.choose_language()
        self.speak(self.responses[self.language]["welcome"])
        self.speak(self.responses[self.language]["prompt"])

        while True:
            query = self.listen()
            if not query:
                self.speak(self.responses[self.language]["prompt"])
                continue
            if _contains_any(query, ("exit", "quit", "bye", "close")):
                self.speak(self.responses[self.language]["goodbye"])
                return 0

            response = self.handle_query(query)
            self.speak(response)
            self.speak(self.responses[self.language]["prompt"])

