import hashlib


def generate_freedom_pay_sig(script_name, params, secret_key):
    # 1. Сортируем ключи в алфавитном порядке
    sorted_keys = sorted(params.keys())

    # 2. Собираем значения параметров в этом порядке
    # Важно: используем только значения
    sorted_values = [str(params[k]) for k in sorted_keys]

    # 3. Формируем строку по правилу: script;params;secret
    # Пример: payment-result;value1;value2;secretkey
    data_list = [script_name] + sorted_values + [secret_key]
    data_str = ";".join(data_list)

    # 4. MD5 хеш
    return hashlib.md5(data_str.encode('utf-8')).hexdigest()