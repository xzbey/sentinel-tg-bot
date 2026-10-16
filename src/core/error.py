class SearchError(Exception):
    ...

class ParseError(Exception):
    ...


def sentinelhub_error(e: Exception) -> SearchError:
    err = str(e)
    
    if "401" in err or "Unauthorized" in err:
        return SearchError("Ошибка авторизации Sentinel Hub (401). Проблема в client_id и client_secret.")
    
    elif "403" in err or "Forbidden" in err:
        if "expired" in err.lower():
            return SearchError("Тестовый период Sentinel Hub истёк (403).")
        return SearchError("Доступ запрещён Sentinel Hub (403). Возможно, закончились токены.")
    
    return SearchError(f"Ошибка Sentinel Hub: {e}")