import os
import time
import threading
import multiprocessing
from queue import Queue
import random


# === Загальні налаштування ===
FOLDER = "files"  # папка з файлами
KEYWORDS = ["OpenMP", "Java", "семафори", "для"]  # ключові слова
NUM_WORKERS = 4  # кількість потоків/процесів


# === Функція для генерації тестових файлів ===
def create_test_files(folder, n=5):
    os.makedirs(folder, exist_ok=True)
    words = ["OpenMP", "Java", "семафори", "для", "стандартах", "random", "text"]
    for i in range(1, n + 1):
        with open(os.path.join(folder, f"file{i}.txt"), "w", encoding="utf-8") as f:
            content = " ".join(random.choices(words, k=100))
            f.write(content)


# === Функція пошуку ключових слів у файлах ===
def search_in_files(file_list, keywords):
    results = {kw: [] for kw in keywords}
    for file_path in file_list:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read().lower()
                for kw in keywords:
                    if kw.lower() in text:
                        results[kw].append(file_path)
        except Exception as e:
            print(f"[ERROR] Не вдалося обробити {file_path}: {e}")
    return results


# === Об’єднання результатів ===
def merge_results(*dicts):
    merged = {}
    for d in dicts:
        for k, v in d.items():
            merged.setdefault(k, []).extend(v)
    return merged


# === THREADING worker ===
def thread_worker(file_subset, keywords, q):
    res = search_in_files(file_subset, keywords)
    q.put(res)


# === MULTIPROCESSING worker ===
def mp_worker(file_subset, keywords, q):
    res = search_in_files(file_subset, keywords)
    q.put(res)


# === Версія 1: Threading ===
def threading_version(files, keywords):
    start_time = time.time()
    chunk_size = max(1, len(files) // NUM_WORKERS)
    threads = []
    results_queue = Queue()

    for i in range(NUM_WORKERS):
        start = i * chunk_size
        end = None if i == NUM_WORKERS - 1 else (i + 1) * chunk_size
        t = threading.Thread(target=thread_worker, args=(files[start:end], keywords, results_queue))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    all_results = []
    while not results_queue.empty():
        all_results.append(results_queue.get())

    merged = merge_results(*all_results)
    exec_time = time.time() - start_time
    return merged, exec_time


# === Версія 2: Multiprocessing ===
def multiprocessing_version(files, keywords):
    start_time = time.time()
    chunk_size = max(1, len(files) // NUM_WORKERS)
    queue = multiprocessing.Queue()
    processes = []

    for i in range(NUM_WORKERS):
        start = i * chunk_size
        end = None if i == NUM_WORKERS - 1 else (i + 1) * chunk_size
        p = multiprocessing.Process(target=mp_worker, args=(files[start:end], keywords, queue))
        processes.append(p)
        p.start()

    for p in processes:
        p.join()

    all_results = []
    while not queue.empty():
        all_results.append(queue.get())

    merged = merge_results(*all_results)
    exec_time = time.time() - start_time
    return merged, exec_time


# === Основний блок ===
if __name__ == "__main__":
    # створюємо тестові файли, якщо їх ще немає
    if not os.path.exists(FOLDER) or not os.listdir(FOLDER):
        print("⚡ Створюю тестові файли...")
        create_test_files(FOLDER, n=8)

    # збір списку файлів
    all_files = [os.path.join(FOLDER, f) for f in os.listdir(FOLDER) if f.endswith(".txt")]

    # Багатопотокова версія
    thread_results, thread_time = threading_version(all_files, KEYWORDS)
    print("\n=== Результати THREADING ===")
    for k, v in thread_results.items():
        print(f"{k}: {v}")
    print(f"Час виконання (threads): {thread_time:.4f} c")

    # Багатопроцесорна версія
    process_results, process_time = multiprocessing_version(all_files, KEYWORDS)
    print("\n=== Результати MULTIPROCESSING ===")
    for k, v in process_results.items():
        print(f"{k}: {v}")
    print(f"Час виконання (processes): {process_time:.4f} c")
