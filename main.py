DATA_PATH = "data/dataset.json"

import json
with open(DATA_PATH, 'r', encoding='utf-8') as f:
    data = json.load(f)

print(f"Всего текстов: {len(data)}")

class FRECalculator:
    @staticmethod
    def count_syllables_ru(word):
        return len(re.findall(r'[аеёиоуыэюя]', word.lower()))
    @staticmethod
    def calculate(text):
        """Реализация Flesch Reading Ease для русского языка"""
        words = re.findall(r'\w+', text)
        sentences = [s for s in re.split(r'(?<=[.!?]) +', text) if s]

        if not words or not sentences:
            return 0.0

        # Подсчет слогов
        syllable_count = sum(FRECalculator.count_syllables_ru(w) for w in words)
        fre = 206.835 - (1.3 * (len(words)/len(sentences))) - (60.1 * (syllable_count/len(words)))
        return max(0, min(round(fre, 1), 100))
    
import re
import pymorphy3
import csv
morph = pymorphy3.MorphAnalyzer()
def load_abbreviations_from_csv(csv_path):
    abbreviation_dict = {}
    with open(csv_path, newline='', encoding='utf-8-sig') as csvfile:
        reader = csv.DictReader(csvfile, delimiter=';')  # меняем на ; !
        # print("Заголовки колонок:", reader.fieldnames)

        for row in reader:
            # print("Строка:", row)
            abbr = row["abbreviation"].strip()
            desc = row["description"].strip()
            if abbr and desc:
                abbreviation_dict[abbr] = desc

    return abbreviation_dict

class TextSimplifier:
    def __init__(self, abbreviation_dict=None, synonym_dict=None):
        self.abbreviation_dict = abbreviation_dict or {}
        self.synonym_dict = synonym_dict or {}
        self.abbreviation_dict = load_abbreviations_from_csv("./abbreviations.csv")
        # print('self.abbreviation_dict',self.abbreviation_dict)

    def simplify(self, text):
        lines = text.split('\n')
        cleaned_lines = [line.strip() for line in lines if line.strip()]
        text = ' '.join(cleaned_lines)
        text = self.expand_abbreviations(text)
        text = self.convert_passive_to_active(text)
        text = self.replace_complex_connectors(text)
        text = self.replace_complex_words(text)
        text = self.remove_redundancies(text)
        return text

    def expand_abbreviations(self, text):
        for abbr, full in self.abbreviation_dict.items():
            try:
                new_text = re.sub(abbr, full, text)
                # if new_text != text:
                    # print(f"🔁 Заменено: '{abbr}' → '{full}'")
                text = new_text
            except re.error:
                continue  # если невалидный regex — пропускаем
        return text

    def convert_passive_to_active(self, text):
        # Пример простейшей замены пассива
        # Можно расширить с помощью NLP-библиотек
        text = re.sub(r'был[ао]? (\w{4,})(?:[а-я]{2,3})?', r'\1', text)
        return text

    def replace_complex_connectors(self, text):
        replacements = {
            "в связи с тем, что": "потому что",
            "в случае, если": "если",
            "осуществляется": "проводится",
            "на основании": "из-за",
            "в соответствии с": "согласно",
        }
        for old, new in replacements.items():
            pattern = r'\b' + re.escape(old) + r'\b'
            text = re.sub(pattern, new, text)
        return text

    def replace_complex_words(self, text):
        for complex_word, simple_word in self.synonym_dict.items():
            pattern = r'\b' + re.escape(complex_word) + r'\b'
            text = re.sub(pattern, simple_word, text)
        return text

    def remove_redundancies(self, text):
        redundancies = [
            r'\bв целом\b',
            r'\bследует отметить\b',
            r'\bв то же время\b',
        ]
        for phrase in redundancies:
            text = re.sub(phrase, '', text)
        return text


LLM_URL = "http://localhost:9005/completions"
HEADERS = {"Content-Type": "application/json"}
MAX_TOKENS = 10000

import re
import requests
import json

class TextRefiner:
    def __init__(self):
        pass  # Никакой модели или токенизатора не требуется
    
    def clean_output(self, text):
        # Удалить маркеры и лишние символы
        text = re.sub(r'^[-•\d\)\s]+', '', text, flags=re.MULTILINE)
        # Удалить лишние пробелы и пустые строки
        text = re.sub(r'\n{2,}', '\n', text)
        text = re.sub(r'\s{2,}', ' ', text)
        return text.strip()

    def refine(self, text):
        # Разделение текста на предложения
        sentences = re.split(r'(?<=[.!?])\s+', text.strip())
        
        simplified_paragraphs = []
        current_paragraph = []
        sentence_count = 0
        
        for sentence in sentences:
            # Пропускаем предложения менее 20 символов
            match = re.search(r'(\b\w{5,})[.!?]$', sentence)
            if len(sentence.strip()) >= 70 or match:
                current_paragraph.append(sentence.strip())
                sentence_count += 1
            else:
                current_paragraph.append(sentence.strip())
                
            
            # Если собрали 4 предложения, отправляем их на обработку
            if sentence_count == 7:
                paragraph = ' '.join(current_paragraph)
                simplified_paragraphs.append(self.process_paragraph(paragraph))
                current_paragraph = []
                sentence_count = 0
        
        # Обработка оставшихся предложений, если есть
        if current_paragraph:
            paragraph = ' '.join(current_paragraph)
            simplified_paragraphs.append(self.process_paragraph(paragraph))
        
        return ' '.join(simplified_paragraphs)

    def process_paragraph(self, paragraph):

        # prompt = f"""
        # Ты — ассистент, который переписывает сложные деловые тексты простым и понятным языком.

        # Твоя цель — сделать текст удобным для чтения, понятным и доступным человеку без специального образования. Пиши так, как будто объясняешь другу. Избегай сухого делового стиля.

        # 🔹 Строго соблюдай следующие правила:

        # 1. Пиши короткими предложениями — до 12–15 слов.
        # 2. Упрощай формулировки. Заменяй сложные слова на простые синонимы.
        # 3. Разделяй громоздкие фразы на простые блоки.
        # 4. Не добавляй ничего от себя. Просто перепиши понятнее.
        # 5. Сохраняй логическую структуру текста.
        # 6. Избегай вводных слов («в целом», «следует отметить» и т.п.).
        # 7. Убирай пассивные конструкции. Используй «кто делает что».
        # 8. Не используй бюрократический стиль.

        # 📈 Цель — добиться высокой прозрачности текста и низкой сложности по шкале читаемости.

        # Пример:
        # Исходный текст: В рамках осуществления проекта были реализованы меры по стабилизации рынка.
        # Понятный вариант: Запустили проект. Он помог стабилизировать рынок.

        # Теперь перепиши этот текст проще и понятнее:
        # {paragraph.strip()}
        # """

        prompt = f"""
        Ты — помощник, который упрощает тексты по правилам ясного и простого языка.

        Твоя задача — переписать текст максимально просто, так чтобы он подходил даже для младших школьников. Используй только самые простые и знакомые слова.

        Строго соблюдай следующие правила:

        1. Разбивай сложные предложения на 2–3 коротких. Не делай предложения длиннее 12 слов.
        2. Избегай редких, длинных и профессиональных слов.
        3. Используй только общеупотребительные слова из повседневного лексикона.
        4. Если есть сложные фразы или обороты — замени их на простые слова.
        5. Повторы допустимы. Главное — чтобы было понятно.
        6. Структура каждого предложения должна быть простой: подлежащее + сказуемое + дополнение.
        7. Не комментируй, не рассуждай, не добавляй нового.
        8. Не объясняй смысл. Просто перепиши проще.
        9. Избегай вводных слов: «в целом», «следует отметить», «в то же время».
        10. **Каждое предложение должно быть коротким и самостоятельным.**

        Твоя цель: чтобы у текста была как можно **ниже сложность** по шкале ARI и как можно **выше оценка прозрачности** по шкале Alina.

        Пример:
        Исходный текст: В рамках осуществления проекта были реализованы меры по стабилизации рынка.
        Ответ: Проект запустили. Он помог стабилизировать рынок.

        Теперь упростите этот текст:
        {paragraph.strip()}
        """

        payload = {
            "prompt": prompt,
            "max_tokens": 512,
            "temperature": 0.7,
            "top_k": 10
        }
        print(f"\n=== Отправка запроса для блока ===")
        print(f"Текст:\n{prompt}\n")
        try:
            response = requests.post(LLM_URL, headers=HEADERS, data=json.dumps(payload))
            response.raise_for_status()
            
            result = response.json()

            content = result.get("content", "").strip()
                        

            lines = content.splitlines()
            cleaned_lines = []

            for i, line in enumerate(lines):
                stripped = line.strip()

                if not stripped:
                    continue  # пропускаем пустые строки

                if i == 0:
                    # Удаляем служебные слова, одинокие символы и лишние префиксы из первой строки
                    cleaned_line = re.sub(r'^(?:[^\wа-яА-Я]*\b)?(Ответ|Answer|output|Упрощённый текст)?[:\-\s_#>]*', '', stripped, flags=re.IGNORECASE)
                    
                    # Если после удаления всё равно остался только одиночный символ — убираем
                    if len(cleaned_line.strip()) <= 2:
                        continue
                else:
                    # Убираем строки из одного символа
                    if len(stripped) <= 2:
                        continue
                    cleaned_line = stripped

                cleaned_lines.append(cleaned_line)

            # Собираем текст в одну строку
            cleaned = " ".join(cleaned_lines).strip()

            # cleaned = self.clean_output(cleaned)
            cleaned = " ".join([line.strip() for line in cleaned.splitlines() if line.strip()])

            print(f"📥 Ответ от модели:\n{cleaned}\n")
            return cleaned
        except Exception as e:
            print(f"❌ Ошибка при обработке блока: {e}")
            return paragraph  # fallback: оригинальный текст
    
import requests
def get_score(model_id, text, auth_token= '4e5f6a7b-8c9d-0e1f-2a3b-4c5d6e7f8a9b'):
  payload = {'model_id':model_id, 'text':text}
  headers = {'Authorization': auth_token}
  resp = requests.post('http://skolkovo.cbrai.ru/api/v1/score', json=payload, headers=headers)
  if resp.status_code == 200:
    return resp.json() ['score']
  else:
    print (f"Error acquired: {resp.status_code}, {resp.text}" )
    return "Error"
  
class Pipeline:
    def __init__(self):
        self.simplifier = TextSimplifier()
        self.refiner = TextRefiner()
        self.fre = FRECalculator()

    def process(self, text):
        # print("=== Исходный текст ===\n", text + "\n")

        # Оценка качества
        orig_metrics = {
            'Alina': get_score('AlinaEstimator', (text)),
            'FRE': self.fre.calculate(text),
            'Arie': get_score('ARIEstimator',(text))
        }


        simplified = self.simplifier.simplify(text)
        intermediate = simplified
        refined = self.refiner.refine(simplified)


        refined_metrics = {
            'Alina': get_score('AlinaEstimator',(refined)),
            'FRE': self.fre.calculate(refined),
            'Arie': get_score('ARIEstimator',(refined))
        }

        return {
            'text': refined,
            'simplified': intermediate,
            'metrics': {
                'original': orig_metrics,
                'simplified': refined_metrics
            }
        }
    
pipeline = Pipeline()

alina_scores_before = []
alina_scores_after = []
arie_scores_before = []
arie_scores_after = []
fre_scores_before = []
fre_scores_after = []

with open("results.txt", "w", encoding="utf-8") as f:
    i = 0  # счётчик обработанных текстов

    for key, item in data.items():
        orig_alina = item.get("AlinaEstimator", 0)

        if orig_alina >= 2:
            continue  # пропускаем тексты с метрикой Alina >= 3

        text = item['text']
        result = pipeline.process(text)

        # Метрики
        simp_alina = result['metrics']['simplified']['Alina']
        orig_arie = result['metrics']['original']['Arie']
        simp_arie = result['metrics']['simplified']['Arie']
        orig_fre = result['metrics']['original']['FRE']
        simp_fre = result['metrics']['simplified']['FRE']

        # Добавляем упрощённый текст в текущий элемент словаря
        item['easy_text'] = result['text']

        # Для подсчёта средних метрик
        alina_scores_before.append(orig_alina)
        alina_scores_after.append(simp_alina)
        arie_scores_before.append(orig_arie)
        arie_scores_after.append(simp_arie)
        fre_scores_before.append(orig_fre)
        fre_scores_after.append(simp_fre)

        i += 1
        # if i >= 10:
        #     break  # только первые 10 подходящих
        print(i)
    # Сохраняем результат в новый файл
    with open("data/updated_dataset.json", "w", encoding="utf-8") as f_out:
        json.dump(data, f_out, ensure_ascii=False, indent=2)

    # Вывод средних метрик
    def avg(lst):
        try:
            numeric = [float(x) for x in lst]
            return round(sum(numeric) / len(numeric), 2) if numeric else 0.0
        except ValueError:
            return 0.0

    print("\n========== СРЕДНИЕ МЕТРИКИ ==========")
    print(f"Alina: {avg(alina_scores_before)} → {avg(alina_scores_after)}")
    print(f"Arie: {avg(arie_scores_before)} → {avg(arie_scores_after)}")
    print(f"FRE: {avg(fre_scores_before)} → {avg(fre_scores_after)}")
