from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any

import aiohttp
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import MODE_LOCAL, MODE_CLOUD


class WiNetApiError(Exception):
    """Generic WiNet API error."""


def _half(v: Any) -> float | None:
    """Convert raw temp (0.5°C units) to °C float.
    Handles None / '---' / empty strings.
    """
    if v is None:
        return None
    if isinstance(v, str) and v.strip() in ("", "---"):
        return None
    try:
        return float(v) / 2.0
    except (TypeError, ValueError):
        return None


@dataclass
class WiNetApi:
    hass: HomeAssistant
    mode: str
    host: str | None = None
    stove_id: str | None = None

    def _session(self) -> aiohttp.ClientSession:
        # usa la sessione condivisa di Home Assistant (best practice)
        return async_get_clientsession(self.hass)

    async def _get_json(self, url: str) -> dict[str, Any]:
        try:
            async with self._session().get(
                url,
                timeout=aiohttp.ClientTimeout(total=8),
            ) as resp:
                if resp.status != 200:
                    raise WiNetApiError(f"HTTP {resp.status} su {url}")
                return await resp.json(content_type=None)

        except asyncio.TimeoutError as e:
            raise WiNetApiError("Timeout chiamando WiNet") from e
        except aiohttp.ClientError as e:
            raise WiNetApiError(f"Errore rete: {e}") from e

    async def _call(self, url: str) -> None:
        # Nel YAML i comandi sono URL GET anche quando 'sembrano' comandi.
        try:
            async with self._session().get(
                url,
                timeout=aiohttp.ClientTimeout(total=8),
            ) as resp:
                if resp.status != 200:
                    raise WiNetApiError(f"HTTP {resp.status} su {url}")

        except asyncio.TimeoutError as e:
            raise WiNetApiError("Timeout inviando comando WiNet") from e
        except aiohttp.ClientError as e:
            raise WiNetApiError(f"Errore rete: {e}") from e

    def _require(self) -> None:
        if self.mode == MODE_LOCAL and not self.host:
            raise WiNetApiError("Host/IP mancante per modalità Locale")
        if self.mode == MODE_CLOUD and not self.stove_id:
            raise WiNetApiError("Stove ID mancante per modalità Cloud")

    async def get_all(self) -> dict[str, Any]:
        """Return a normalized dict of status data."""
        self._require()

        if self.mode == MODE_LOCAL:
            url = f"http://{self.host}/api/global"
            data = await self._get_json(url)

            return {
                "raw": data,
                "status": data.get("status"),
                "description": data.get("description"),
                "power": data.get("power"),
                # mezzi gradi -> °C
                "air": _half(data.get("air")),
                "setAir": _half(data.get("setAir")),
                "water": _half(data.get("water")),
                "setWater": _half(data.get("setWater")),
                # altri valori (qui NON applichiamo conversioni)
                "gasflue": data.get("gasflue"),
                "rpmExtractor": data.get("rpmExtractor"),
            }

        # CLOUD
        base = "https://ws.cloudwinet.it/WiNetStove.svc/json"
        stove_id = self.stove_id

        status = await self._get_json(f"{base}/GetStatus/{stove_id}")
        power = await self._get_json(f"{base}/GetPower/{stove_id}")
        air = await self._get_json(f"{base}/GetActualTemperature/{stove_id}")
        set_air = await self._get_json(f"{base}/GetTemperature/{stove_id}")

        return {
            "raw": {"status": status, "power": power, "air": air, "setAir": set_air},
            "status": status.get("Status"),
            "power": power.get("Result"),
            "air": air.get("Result"),
            "setAir": set_air.get("Result"),
        }

    async def ignite(self) -> None:
        self._require()
        if self.mode == MODE_LOCAL:
            await self._call(f"http://{self.host}/api/status/1")
        else:
            await self._call(f"https://ws.cloudwinet.it/WiNetStove.svc/json/Ignit/{self.stove_id}")

    async def shutdown(self) -> None:
        self._require()
        if self.mode == MODE_LOCAL:
            await self._call(f"http://{self.host}/api/status/0")
        else:
            await self._call(f"https://ws.cloudwinet.it/WiNetStove.svc/json/Shutdown/{self.stove_id}")

    async def set_power(self, level: int) -> None:
        # range deciso: 1..5
        if level < 1 or level > 5:
            raise WiNetApiError("Power fuori range (1–5)")

        self._require()

        if self.mode == MODE_LOCAL:
            await self._call(f"http://{self.host}/api/power/{level}")
        else:
            await self._call(f"https://ws.cloudwinet.it/WiNetStove.svc/json/SetPower/{self.stove_id};{level}")

    async def set_air_temperature(self, temp_c: float) -> None:
        self._require()
        if self.mode == MODE_LOCAL:
            # °C -> mezzi gradi (intero)
            raw = int(round(float(temp_c) * 2))
            await self._call(f"http://{self.host}/api/temperature/air/{raw}")
        else:
            await self._call(
                f"https://ws.cloudwinet.it/WiNetStove.svc/json/SetTemperature/{self.stove_id};{float(temp_c)}"
            )

    async def set_water_temperature(self, temp_c: float) -> None:
        """Set water temperature (Local only)."""
        self._require()
        if self.mode == MODE_LOCAL:
            raw = int(round(float(temp_c) * 2))
            await self._call(f"http://{self.host}/api/temperature/water/{raw}")
        else:
            raise WiNetApiError("Set temperatura acqua non supportato in Cloud (manca endpoint)")
