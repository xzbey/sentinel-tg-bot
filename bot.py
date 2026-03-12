from geo_search import search

def print_data(results):
    if results["success"]:
        print(f"Адрес: {results['data']['address']}\n" +
              f"Координаты: {results['data']['coords']}\n" +
              f"Метаданные снимка: {results['data']['metadata']}\n" +
              f"Разрешение: {results['data']['resolution']} м\n" +
              f"Размер: {results['data']['size']} пикселей")
        results['data']['image'].show()
    else:
        print(f"Ошибка: {results['error']}")


#print_data(search("алешинские сады"))
print_data(search("авиаторов 5", time_interval=("2025-06-01", "2025-08-31")))