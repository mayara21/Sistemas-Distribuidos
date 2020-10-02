from dataclasses import dataclass

@dataclass
class User:
    name: str
    ip_address: str
    port: int