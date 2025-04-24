def fetch_debug(url, method, data) -> str:
    return f'method={method} len(data)={len(data)} url=`{url}` data=`{data[:100]}`'
