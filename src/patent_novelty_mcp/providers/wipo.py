from __future__ import annotations

import atexit
import os
import re
import time
from typing import Any, Dict

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait

from patent_novelty_mcp.core.models import ProviderResult
from patent_novelty_mcp.providers.base import BaseProvider


class WipoPatentscopeProvider(BaseProvider):
    name = "wipo_patentscope"

    def __init__(self) -> None:
        self._username = ""
        self._password = ""
        self._driver = None
        self._wait = None
        self._is_authenticated = False
        self._last_query_ts = 0.0
        atexit.register(self._shutdown)

    def capabilities(self) -> Dict[str, Any]:
        return {
            "smiles": True,
            "inchi": True,
            "inn": True,
            "compound_name": True,
            "scaffold_mode": True,
            "batch": True,
            "auth_required": True,
        }

    def auth(self, creds: Dict[str, Any]) -> None:
        username = str(creds.get("username", "")).strip()
        password = str(creds.get("password", "")).strip()
        if not username or not password:
            raise ValueError("WIPO credentials are required")
        creds_changed = username != self._username or password != self._password
        self._username = username
        self._password = password
        if creds_changed:
            self._is_authenticated = False

        self._ensure_driver()
        if not self._is_authenticated:
            self._login()

    def check_compliance(self, request: Dict[str, Any]) -> None:
        query_type = str(request.get("query_type", "")).lower()
        if query_type not in {"smiles", "inchi", "inn", "compound_name"}:
            raise ValueError(f"Unsupported query_type for WIPO provider: {query_type}")
        return

    def normalize_query(self, query: str, query_type: str) -> str:
        return query.strip()

    def query(self, query: str, query_type: str, options: Dict[str, Any]) -> ProviderResult:
        self._ensure_driver()
        if not self._is_authenticated:
            self._login()

        # Light client-side throttling.
        now = time.time()
        min_interval = float(options.get("min_interval_seconds", 0.3))
        if now - self._last_query_ts < min_interval:
            time.sleep(min_interval - (now - self._last_query_ts))
        self._last_query_ts = time.time()

        max_attempts = int(options.get("query_attempts", 2))
        for attempt in range(1, max_attempts + 1):
            try:
                result = self._query_once(query, query_type, options)
            except Exception as exc:
                if isinstance(exc, StaleElementReferenceException) or "stale element reference" in str(exc).lower():
                    if attempt < max_attempts:
                        continue
                    result = self._error_result(f"WIPO query failed after stale retries: {exc}")
                else:
                    # Retry once if session likely expired.
                    msg = str(exc).lower()
                    if ("authpage" in msg or "signin" in msg or "login" in msg) and attempt < max_attempts:
                        self._is_authenticated = False
                        self._login()
                        continue
                    result = self._error_result(f"WIPO query failed: {exc}")

            if (
                query_type.lower() == "inn"
                and result.status == "invalid_query"
                and result.error
                and "please enter a search term" in result.error.lower()
            ):
                # Stabilize INN path by trying COMPOUND mode fallback.
                fallback_options = dict(options)
                fallback_options["force_search_type"] = "COMPOUND"
                try:
                    result = self._query_once(query, query_type, fallback_options)
                except Exception as exc:
                    result = self._error_result(f"WIPO INN fallback failed: {exc}")

            # Transient blank-query UI path: retry with full page reload.
            if (
                result.status == "invalid_query"
                and result.error
                and "please enter a search term" in result.error.lower()
                and attempt < max_attempts
            ):
                continue

            return result

        # Safety fallback (should not be reached).
        return self._error_result("WIPO query failed after retry budget")

    def _ensure_driver(self) -> None:
        if self._driver is not None and self._wait is not None:
            return

        opts = Options()
        headless = os.environ.get("WIPO_HEADLESS", "1").strip() not in {"0", "false", "False"}
        if headless:
            opts.add_argument("--headless=new")
        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-dev-shm-usage")
        self._driver = webdriver.Chrome(options=opts)
        self._wait = WebDriverWait(self._driver, int(os.environ.get("WIPO_TIMEOUT", "60")))

    def _shutdown(self) -> None:
        if self._driver is not None:
            try:
                self._driver.quit()
            except Exception:
                pass
        self._driver = None
        self._wait = None
        self._is_authenticated = False

    def _login(self) -> None:
        assert self._driver is not None
        assert self._wait is not None
        self._driver.get("https://patentscope.wipo.int/search/en/chemc/chemc.jsf")
        self._wait.until(
            EC.presence_of_element_located((By.ID, "authform_fields:0:authform_text:input"))
        ).send_keys(self._username)
        self._driver.find_element(By.ID, "authform_fields:1:authform_mask:input").send_keys(self._password)
        self._driver.find_element(By.ID, "authform_signin").click()
        self._wait.until(lambda d: "patentscope.wipo.int/search" in d.current_url)
        self._is_authenticated = True

    def _open_chemical_search(self) -> None:
        assert self._driver is not None
        assert self._wait is not None
        self._driver.get("https://patentscope.wipo.int/search/en/chemc/chemc.jsf")
        self._wait.until(EC.presence_of_element_located((By.ID, "chemcForm:searchByCombo:input")))

    def _set_checkbox(self, elem_id: str, checked: bool = True) -> None:
        assert self._driver is not None
        self._driver.execute_script(
            """
            const el = document.getElementById(arguments[0]);
            if (el) {
              el.checked = arguments[1];
              el.dispatchEvent(new Event('change', { bubbles: true }));
            }
            """,
            elem_id,
            checked,
        )

    def _set_search_type(self, search_type: str) -> None:
        assert self._driver is not None
        assert self._wait is not None
        select_el = self._wait.until(EC.presence_of_element_located((By.ID, "chemcForm:searchByCombo:input")))
        Select(select_el).select_by_value(search_type)
        # wait for value to settle after ajax update
        self._wait.until(lambda d: d.find_element(By.ID, "chemcForm:searchByCombo:input").get_attribute("value") == search_type)
        time.sleep(0.25)

    def _set_query_text(self, query: str) -> None:
        assert self._driver is not None
        assert self._wait is not None
        qinput = self._wait.until(EC.presence_of_element_located((By.ID, "chemcForm:search:input")))
        try:
            qinput.clear()
            qinput.send_keys(query)
        except StaleElementReferenceException:
            qinput = self._wait.until(EC.presence_of_element_located((By.ID, "chemcForm:search:input")))
            qinput.clear()
            qinput.send_keys(query)

        # Defensive set + verify in case rerender wipes text.
        self._driver.execute_script(
            """
            const el = document.getElementById('chemcForm:search:input');
            if (el) {
              el.value = arguments[0];
              el.dispatchEvent(new Event('input', { bubbles: true }));
              el.dispatchEvent(new Event('change', { bubbles: true }));
            }
            """,
            query,
        )
        self._wait.until(
            lambda d: (d.find_element(By.ID, "chemcForm:search:input").get_attribute("value") or "").strip() == query
        )

    def _submit_search(self) -> None:
        assert self._driver is not None
        # JS click is more reliable when overlays/tooltips intercept.
        self._driver.execute_script(
            """
            const el = document.getElementById('chemcForm:convertStructureSearch');
            if (el) { el.click(); }
            """
        )

    def _query_once(self, query: str, query_type: str, options: Dict[str, Any]) -> ProviderResult:
        assert self._driver is not None
        self._open_chemical_search()

        qtype = query_type.lower()
        # WIPO chemical search types are: COMPOUND, INN, INCHI, SMILES.
        # In practice, INN UI path is unstable in headless automation; we route `inn` to COMPOUND.
        forced = str(options.get("force_search_type", "")).strip().upper()
        if forced in {"SMILES", "INCHI", "INN", "COMPOUND"}:
            search_type = forced
        else:
            if qtype == "smiles":
                search_type = "SMILES"
            elif qtype == "inchi":
                search_type = "INCHI"
            elif qtype == "inn":
                search_type = "COMPOUND"
            elif qtype == "compound_name":
                search_type = "COMPOUND"
            else:
                raise ValueError(f"Unsupported query_type for WIPO provider: {query_type}")
        self._set_search_type(search_type)
        self._set_query_text(query)

        scaffold_mode = bool(options.get("scaffold_mode", False))
        include_markush = bool(options.get("include_markush_enumeration", False))
        # Always set both to avoid state bleed between queries.
        self._set_checkbox("chemcForm:scaffold:input", scaffold_mode)
        self._set_checkbox("chemcForm:includeMEIS:input", include_markush)

        self._submit_search()

        timeout = int(options.get("timeout_seconds", 60))
        deadline = time.time() + timeout
        while time.time() < deadline:
            url = self._driver.current_url
            body = self._driver.find_element(By.TAG_NAME, "body").text
            body_lower = body.lower()
            page_source = self._driver.page_source
            source_lower = page_source.lower()

            if "/result.jsf" in url:
                count = self._extract_result_count(body, page_source)
                if count is not None:
                    return ProviderResult(
                        provider=self.name,
                        status="ok",
                        hit=count > 0,
                        result_count=count,
                        novelty_score=0 if count > 0 else 1,
                        confidence=0.98,
                        evidence={
                            "url": url,
                            "snippet": f"{count} results",
                            "search_type": search_type,
                            "scaffold_mode": scaffold_mode,
                            "include_markush_enumeration": include_markush,
                        },
                        error=None,
                    )
                if "no results were found" in body_lower or "no results were found" in source_lower:
                    return ProviderResult(
                        provider=self.name,
                        status="ok",
                        hit=False,
                        result_count=0,
                        novelty_score=1,
                        confidence=0.95,
                        evidence={
                            "url": url,
                            "snippet": "No results were found to match your search",
                            "search_type": search_type,
                            "scaffold_mode": scaffold_mode,
                            "include_markush_enumeration": include_markush,
                        },
                        error=None,
                    )
                # Fallback: if tabular results are visible, treat as a hit even when total count is not parseable.
                row_count = len(self._driver.find_elements(By.CSS_SELECTOR, "table tbody tr"))
                if row_count > 0:
                    return ProviderResult(
                        provider=self.name,
                        status="ok",
                        hit=True,
                        result_count=row_count,
                        novelty_score=0,
                        confidence=0.7,
                        evidence={
                            "url": url,
                            "snippet": f"rows_on_page={row_count}",
                            "search_type": search_type,
                            "scaffold_mode": scaffold_mode,
                            "include_markush_enumeration": include_markush,
                        },
                        error=None,
                    )

            if "/chemc/chemc.jsf" in url and "structure could not be resolved" in body_lower:
                return ProviderResult(
                    provider=self.name,
                    status="invalid_query",
                    hit=None,
                    result_count=None,
                    novelty_score=None,
                    confidence=None,
                    evidence={"url": url, "snippet": "The structure could not be resolved."},
                    error="The structure could not be resolved",
                )

            if "/chemc/chemc.jsf" in url and "please enter a search term" in body_lower:
                return ProviderResult(
                    provider=self.name,
                    status="invalid_query",
                    hit=None,
                    result_count=None,
                    novelty_score=None,
                    confidence=None,
                    evidence={"url": url, "snippet": "Please enter a search term"},
                    error="Please enter a search term",
                )

            if "authpage/signin.xhtml" in url:
                raise RuntimeError("Redirected to login page during query")

            time.sleep(0.4)

        return ProviderResult(
            provider=self.name,
            status="timeout",
            hit=None,
            result_count=None,
            novelty_score=None,
            confidence=None,
            evidence={"url": self._driver.current_url, "snippet": "timeout"},
            error="Timed out waiting for result page",
        )

    def _error_result(self, message: str) -> ProviderResult:
        return ProviderResult(
            provider=self.name,
            status="error",
            hit=None,
            result_count=None,
            novelty_score=None,
            confidence=None,
            evidence={},
            error=message,
        )

    @staticmethod
    def _extract_result_count(body_text: str, page_source: str) -> int | None:
        patterns = [
            r"([0-9][0-9,]*)\s+results",
            r"([0-9][0-9,]*)\s+result",
        ]
        haystacks = [body_text, page_source]
        for text in haystacks:
            text_norm = text.replace("\xa0", " ")
            for pat in patterns:
                m = re.search(pat, text_norm, flags=re.IGNORECASE)
                if m:
                    try:
                        return int(m.group(1).replace(",", ""))
                    except ValueError:
                        continue
        return None
