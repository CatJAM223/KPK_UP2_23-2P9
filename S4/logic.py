from models import Permission

def check_url(request_url: str, template_url: str):
    template_segment = template_url.strip('/').split('/')
    request_segment = request_url.strip('/').split('/')
    if len(template_segment) != len(request_segment):
        return False
    else:
        for t_segment, r_segment in zip(template_segment, request_segment):
            if t_segment == '*':
                continue
            if t_segment != r_segment:
                return False
        return True

async def check_permission(role_id: int, method: str , url: str) -> dict[str, bool]:
    action = f"{method} {url}"
    for permission in Permission.select().where(
            (Permission.role_id == role_id)&
            (Permission.method == method)):
        check = check_url(url,permission.url)
        if check:
            return {
                'status_code': 200,
                'allowed': True
            }

    return {
        'status_code': 403,
        'allowed': False,
        'reason': f"Действие {action} не разрешено"
    }
