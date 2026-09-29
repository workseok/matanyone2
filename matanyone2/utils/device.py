import contextlib
import torch
import functools

def get_default_device():
    """mps(Apple Silicon GPU)를 먼저 시도하고, 이 시스템에서 지원하지 않거나
    실제 연산 중 런타임 오류가 나면 자동으로 cpu로 전환합니다.

    torch.backends.mps.is_available()만으로는 빌드 시점 지원 여부만 알 수
    있고 실제 커널 실행 중 발생하는 오류는 잡지 못하므로, 작은 텐서 연산을
    한 번 실행해 확인합니다.
    """
    try:
        if not (torch.backends.mps.is_built() and torch.backends.mps.is_available()):
            raise RuntimeError("이 시스템에서 MPS 백엔드를 사용할 수 없습니다.")
        device = torch.device("mps")
        torch.zeros(1, device=device)  # 실제 동작 여부 확인
        return device
    except Exception:
        return torch.device("cpu")

def safe_autocast_decorator(enabled=True):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            device = get_default_device()
            if device.type in ["cuda", "cpu"]:
                with torch.amp.autocast(device_type=device.type, enabled=enabled):
                    return func(*args, **kwargs)
            else:
                return func(*args, **kwargs)
        return wrapper
    return decorator

@contextlib.contextmanager
def safe_autocast(enabled=True):
    device = get_default_device()
    if device.type in ["cuda", "cpu"]:
        with torch.amp.autocast(device_type=device.type, enabled=enabled):
            yield
    else:
        yield  # MPS or other unsupported backends skip autocast
