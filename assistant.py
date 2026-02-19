import requests
import asyncio
import edge_tts
import subprocess
import random
import re
import os

# ===========================
# CONFIG
# ===========================
MODEL = "llama3.1:8b"  # High quality free model - excellent for multilingual
# Alternative options to try:
# MODEL = "llama3.1:8b"
# MODEL = "qwen2.5:7b-instruct"
# MODEL = "gemma2:9b"
# MODEL = "deepseek-coder-v2:16b"  # Good for technical tasks

# Voice configurations by language
VOICES = {
    "th": {"male": "th-TH-NiwatNeural", "female": "th-TH-PremwadeeNeural", "rate": "-15%"},
    "en": {"male": "en-US-GuyNeural", "female": "en-US-JennyNeural", "rate": "+0%"},
    "zh": {"male": "zh-CN-YunxiNeural", "female": "zh-CN-XiaoxiaoNeural", "rate": "+0%"},
    "ja": {"male": "ja-JP-KeitaNeural", "female": "ja-JP-NanamiNeural", "rate": "+0%"},
    "ko": {"male": "ko-KR-HyunjunNeural", "female": "ko-KR-SunHiNeural", "rate": "+0%"},
    "es": {"male": "es-ES-AlvaroNeural", "female": "es-ES-ElviraNeural", "rate": "+0%"},
    "fr": {"male": "fr-FR-HenriNeural", "female": "fr-FR-DeniseNeural", "rate": "+0%"},
    "de": {"male": "de-DE-ConradNeural", "female": "de-DE-KatjaNeural", "rate": "+0%"},
    "lo": {"male": "th-TH-NiwatNeural", "female": "th-TH-PremwadeeNeural", "rate": "-15%"},  # Lao uses Thai voice
}

VOICE_TH_MALE = "th-TH-NiwatNeural"
VOICE_TH_FEMALE = "th-TH-PremwadeeNeural"
RATE_TH = "-15%"
# MAX_CHARS = 260  # Removed - let AI speak naturally

PERSONA = os.getenv("ASSISTANT_PERSONA", "random").strip().lower()

def pick_persona() -> str:
 if PERSONA in ("male", "female"):
  return PERSONA
 return random.choice(["male", "female"])

ASSISTANT_GENDER = pick_persona()
ENDING = "ครับ" if ASSISTANT_GENDER == "male" else "ค่ะ"
VOICE_TH = VOICE_TH_MALE if ASSISTANT_GENDER == "male" else VOICE_TH_FEMALE

# ===========================
# LLM
# ===========================
def build_prompt(user_text: str) -> str:
 # Detect user language and set response language accordingly
 user_lang = detect_language(user_text)
 lang_instructions = {
     "th": "ตอบเป็นภาษาไทยธรรมชาติ เหมือนคนไทยจริงๆ ใช้การเว้นวรรคและวรรคตอนที่ถูกต้อง",
     "lo": "ຕອບເປັນພາສາລາວທຳມະຊາດ ເໝືອນຄົນລາວຈິງ",
     "zh": "用自然中文回答，像母语者一样，注意标点符号和空格",
     "ja": "自然な日本語で回答してください。句読点とスペースを正しく使ってください",
     "ko": "자연스러운 한국어로 답변해주세요. 띄어쓰기와 문장부호를 정확하게 사용해주세요",
     "es": "Responde en español natural como un hablante nativo, usando espacios y puntuación correctos",
     "fr": "Réponds en français naturel comme un locuteur natif, avec des espaces et ponctuation corrects",
     "de": "Antworte auf natürliches Deutsch wie ein Muttersprachler, mit korrekten Abständen und Zeichensetzung",
     "en": "Respond in natural English like a native speaker, with proper spacing and punctuation"
 }

 lang_endings = {
     "th": "ครับ" if ASSISTANT_GENDER == "male" else "ค่ะ",
     "lo": "ຄ່າ" if ASSISTANT_GENDER == "male" else "ຄ່າ",
     "zh": "。" if ASSISTANT_GENDER == "male" else "。",
     "ja": "です" if ASSISTANT_GENDER == "male" else "です",
     "ko": "입니다" if ASSISTANT_GENDER == "male" else "입니다",
     "es": "." if ASSISTANT_GENDER == "male" else ".",
     "fr": "." if ASSISTANT_GENDER == "male" else ".",
     "de": "." if ASSISTANT_GENDER == "male" else ".",
     "en": "." if ASSISTANT_GENDER == "male" else "."
 }

 instruction = lang_instructions.get(user_lang, "Respond in natural English")
 ending = lang_endings.get(user_lang, ".")

 return (
  f"คุณเป็นผู้ช่วย AI ระดับสูง ควบคุมระบบ smart home พูดภาษาต่างๆ ได้เป็นอย่างดี "
  f"{instruction} ตอบตรงๆ สั้นกระชับ แต่ให้ข้อมูลครบถ้วน "
  f"ใช้คำลงท้าย {ending} "
  f"ผู้ใช้: {user_text}\n"
  f"ผู้ช่วย:"
 )

def ask_llm(text):
 prompt = build_prompt(text)
 r = requests.post(
  "http://localhost:11434/api/generate",
  json={
   "model": MODEL,
   "prompt": prompt,
   "stream": False,
   "options": {"temperature": 0.6, "top_p": 0.9}
  },
  timeout=120
 )
 r.raise_for_status()
 return r.json().get("response", "").strip()

# ===========================
# POST-PROCESS
# ===========================
def normalize_for_tts(text: str) -> str:
 if not text:
  return f"ขอโทษ{ENDING} ตอนนี้ตอบไม่ทัน ลองใหม่อีกครั้งนะ{ENDING}"

 text = re.sub(r"\s+", " ", text).strip()

 text = re.sub(r"```.*?```", " ", text)
 text = text.replace("`", "")

 # Don't modify endings - let AI handle them naturally
 return text

# ===========================
# LANGUAGE DETECTION
# ===========================
def detect_language(text: str) -> str:
    # Simple language detection based on character patterns
    thai_chars = set("กขฃคฅฆงจฉชซฌญฎฏฐฑฒณดตถทธนบปผฝพฟภมยรลวศษสหฬอฮฯๆ๏๐๑๒๓๔๕๖๗๘๙๚๛")
    lao_chars = set("ກຂຄງຈຊຍດຕຖທນບປຜຝພຟຠມຢຣລວສຫອຮຯໆ໐໑໒໓໔໕໖໗໘໙໚໛")
    chinese_chars = set(
        "的一是在不了有和人这中大为上个国我以要他时来用们生到作地于出就分对成会可主发年动同工也能下过子说产种面而方后多定行学法所民得经十三之进着等部度家电力里如水化高自二理起小物现实加量都两体制机当使点从业本去把性好应开它合还因由其些然前外天政四日那社义事平形相全表间样与关各重新线内数正心反你明看原又么利比或但质气第向道命此变条只没结解问意建月公无系军很情者最立代想已通并提直题党程展五果料象员革位入常文总次品式活设及管特件长求老头基资边流路级少图山统接知较将组见计别她手角期根论运农指几九区强放决西被干做必战先回则任取据处队南给色光门即保治北造百规热领七海口东导器压志世金增争济阶油思术极交受联什认六共权收证改清己美再采转更单风切打白教速花带安场身车例真务具万每目至达走积示议声报斗完类八离华名确才科张信马节话米整空元况今集温传土许步群广石记需段研界拉林律叫且究观越织装影算低持音众书布复容儿须际商非验连断深难近矿千周委素技备半办青省列习响约支般史感劳便团往酸历市克何除消构府称太准精值号率族维划选标写存候毛亲快效斯院查江型眼王按格养易置派层片始却专状育厂京识适属圆包火住调满县局照参红细引听该铁价严龙飞"
    )
    japanese_chars = set("あいうえおかきくけこさしすせそたちつてとなにぬねのはひふへほまみむめもやゆよらりるれろわをんアイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワヲン")
    korean_chars = set("가나다라마바사아자차카타파하거너더러머버서어저커타퍼허기니디리미비시이지치키티피히구누두루무부수우주추쿠투푸후그느드르므브스으즈츠크트프호교료무보소오조초코포호")

    text_chars = set(text)

    # Count characters for each language
    thai_count = len(text_chars & thai_chars)
    lao_count = len(text_chars & lao_chars)
    chinese_count = len(text_chars & chinese_chars)
    japanese_count = len(text_chars & japanese_chars)
    korean_count = len(text_chars & korean_chars)

    # Determine language based on character counts
    if lao_count > 0:
        return "lo"
    elif thai_count > 0:
        return "th"
    elif chinese_count > 0:
        return "zh"
    elif japanese_count > 0:
        return "ja"
    elif korean_count > 0:
        return "ko"
    else:
        return "en"  # Default to English for Latin script

# ===========================
# TTS
# ===========================
async def speak(text):
    lang = detect_language(text)
    voice_config = VOICES.get(lang, VOICES["en"])
    voice = voice_config[ASSISTANT_GENDER]
    rate = voice_config["rate"]

    # Special handling for Lao - transliterate to Thai for TTS
    if lang == "lo":
        # Lao to Thai transliteration mapping
        lao_to_thai = {
            'ກ': 'ก', 'ຂ': 'ค', 'ຄ': 'ค', 'ງ': 'ง', 'ຈ': 'จ', 'ຊ': 'ช', 'ຍ': 'ญ',
            'ດ': 'ด', 'ຕ': 'ต', 'ຖ': 'ถ', 'ທ': 'ท', 'ນ': 'น', 'ບ': 'บ', 'ປ': 'ป',
            'ຜ': 'ผ', 'ຝ': 'ฝ', 'ພ': 'พ', 'ຟ': 'ฟ', 'ມ': 'ม', 'ຢ': 'ย', 'ຣ': 'ร',
            'ລ': 'ล', 'ວ': 'ว', 'ສ': 'ส', 'ຫ': 'ห', 'ອ': 'อ', 'ຮ': 'ฮ',
            'ຯ': 'ฯ', 'ໆ': 'ๆ', '໐': '๐', '໑': '๑', '໒': '๒', '໓': '๓', '໔': '๔',
            '໕': '๕', '໖': '๖', '໗': '๗', '໘': '๘', '໙': '๙', '໚': '๚', '໛': '๛',
            'ະ': 'ะ', 'ັ': 'ั', 'າ': 'า', 'ຳ': 'ำ', 'ິ': 'ิ', 'ີ': 'ี',
            'ຶ': 'ึ', 'ື': 'ื', 'ຸ': 'ุ', 'ູ': 'ู', 'ົ': '๋', 'ຼ': '๊',
            'ໍ': '็', '່': '่', '້': '้', '໊': '๊', '໋': '๋'
        }

        # Transliterate Lao to Thai
        thai_text = ""
        for char in text:
            thai_text += lao_to_thai.get(char, char)

        print(f"[Lao → Thai]: {thai_text}")
        text = thai_text
        voice = VOICES["th"][ASSISTANT_GENDER]  # Use Thai voice
        rate = VOICES["th"]["rate"]

    # print(f"Detected language: {lang}, using voice: {voice}")  # Debug info
    communicate = edge_tts.Communicate(
        text,
        voice,
        rate=rate,
    )
    out = "response.mp3"
    try:
        await communicate.save(out)
        subprocess.run(["mpg123", "-q", out], check=False)
    except Exception as e:
        print(f"TTS Error: {e}")
        print("Falling back to print-only mode")

# ===========================
# MAIN
# ===========================
def main():
 print(f"Persona: {ASSISTANT_GENDER} / ending: {ENDING} / voice: {VOICE_TH}")
 while True:
  user = input("You: ").strip()
  if not user:
   continue
  if user.lower() in ("exit", "quit"):
   break

  try:
   ai_response = ask_llm(user)
  except Exception as e:
   ai_response = f"ขอโทษ{ENDING} ระบบ LLM มีปัญหานิดหน่อย{ENDING}"

  tts_text = normalize_for_tts(ai_response)

  # Show response immediately
  print(f"AI: {ai_response}")

  # Start TTS in background thread (non-blocking)
  import threading
  tts_thread = threading.Thread(target=lambda: asyncio.run(speak(tts_text)))
  tts_thread.daemon = True
  tts_thread.start()

if __name__ == "__main__":
 main()
