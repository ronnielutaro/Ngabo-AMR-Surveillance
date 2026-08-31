"""Ngabo Connect desktop client — folder watch + auto-upload (Epic #171).

One window: pick a watched folder, hit Start. Any new ``.csv`` export dropped in
is SHA-256'd, queued locally (durable SQLite), and uploaded to a configurable
intake endpoint (HMAC-signed). Ngabo takes over from there. Stdlib only.

Run:  python scripts/ngabo_connect_desktop.py
Config via env:  NGABO_INTAKE_URL, NGABO_LAB_ID, NGABO_SOURCE_ID, NGABO_HMAC_SECRET
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import threading
import time
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, ttk
from urllib import request
from urllib.parse import urlsplit

DEFAULT_INTAKE_URL = "https://ngabo-core-2zhvmdaotq-uc.a.run.app/connect/batches"
DEFAULT_INVOKER_SERVICE_ACCOUNT = (
    "ngabo-connect-demo@ngabo-amr-2026.iam.gserviceaccount.com"
)

_SERVICE_CORE = Path(__file__).resolve().parents[1] / "services" / "core"
sys.path.insert(0, str(_SERVICE_CORE))

from ngabo.infrastructure.connect.connect_queue import ConnectQueue  # noqa: E402
from ngabo.infrastructure.connect.edge import file_sha256, stable_size_mtime  # noqa: E402
from ngabo.infrastructure.connect.hmac_auth import compute_signature  # noqa: E402


class ConnectApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("NGABO CONNECT")
        self.geometry("620x380")
        self.watch_dir: Path | None = None
        self.queue: ConnectQueue | None = None
        self.running = False
        self._build_ui()

    def _build_ui(self) -> None:
        frame = ttk.Frame(self, padding=16)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text="NGABO CONNECT", font=("Segoe UI", 16, "bold")).grid(
            row=0, column=0, columnspan=2, sticky="w"
        )
        ttk.Label(frame, text="Laboratory: Synthetic Surveillance Lab — Gulu").grid(
            row=1, column=0, columnspan=2, sticky="w", pady=(4, 12)
        )
        ttk.Label(frame, text="Watched folder:").grid(row=2, column=0, sticky="w")
        self.folder_var = tk.StringVar(value="(not selected)")
        ttk.Entry(frame, textvariable=self.folder_var, width=48).grid(
            row=2, column=1, sticky="ew", padx=(6, 0)
        )
        ttk.Button(frame, text="Choose Folder", command=self._choose_folder).grid(
            row=3, column=0, columnspan=2, sticky="w", pady=6
        )
        ttk.Button(frame, text="Start Watching", command=self._start).grid(
            row=4, column=0, sticky="w"
        )
        self.status_var = tk.StringVar(value="● Offline")
        ttk.Label(frame, textvariable=self.status_var).grid(
            row=4, column=1, sticky="w", padx=8
        )
        self.log = tk.Text(frame, height=12, width=72, state="disabled")
        self.log.grid(row=5, column=0, columnspan=2, sticky="nsew", pady=(12, 0))
        frame.columnconfigure(1, weight=1)
        frame.rowconfigure(5, weight=1)

    def _log(self, message: str) -> None:
        self.log.configure(state="normal")
        self.log.insert("end", f"{time.strftime('%H:%M:%S')}  {message}\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def _choose_folder(self) -> None:
        selected = filedialog.askdirectory(title="Choose watched folder")
        if selected:
            self.watch_dir = Path(selected)
            self.folder_var.set(str(self.watch_dir))
            self._log(f"Watched folder: {self.watch_dir}")

    def _start(self) -> None:
        if self.watch_dir is None:
            self._log("Choose a watched folder first.")
            return
        if self.running:
            self._log("Already watching.")
            return
        self.watch_dir.mkdir(parents=True, exist_ok=True)
        self.queue = ConnectQueue(self.watch_dir / "connect_queue.sqlite")
        self.running = True
        self.status_var.set("● Watching")
        self._log("Watching for new .csv exports. Drop a file to begin.")
        threading.Thread(target=self._watch_loop, daemon=True).start()

    def _watch_loop(self) -> None:
        intake_url = os.environ.get("NGABO_INTAKE_URL", DEFAULT_INTAKE_URL)
        lab_id = os.environ.get("NGABO_LAB_ID", "synthetic-lab-gulu")
        source_id = os.environ.get("NGABO_SOURCE_ID", "whonet-demo")
        secret = os.environ.get("NGABO_HMAC_SECRET", "demo-secret").encode("utf-8")
        while self.running and self.queue is not None:
            try:
                self._scan_and_upload(intake_url, lab_id, source_id, secret)
            except Exception as exc:  # noqa: BLE001
                self.after(0, self._log, f"loop error: {exc}")
            time.sleep(1.0)

    def _scan_and_upload(
        self, intake_url: str, lab_id: str, source_id: str, secret: bytes
    ) -> None:
        assert self.watch_dir is not None and self.queue is not None
        for path in sorted(self.watch_dir.glob("*.csv")):
            if not stable_size_mtime(path):
                continue
            sha = file_sha256(path)
            self.after(0, self._log, f"DETECTED {path.name} sha256={sha[:12]}…")
            self.queue.add(
                file_path=str(path), file_sha256=sha, lab_id=lab_id, source_id=source_id
            )
            while True:
                item = self.queue.next_due()
                if item is None:
                    break
                self.queue.mark_syncing(item["id"])
                queued_path = Path(str(item["file_path"]))
                body = queued_path.read_bytes()
                queued_sha = str(item["file_sha256"])
                filename = queued_path.name
                ts = str(int(time.time()))
                signature = compute_signature(
                    secret, lab_id, source_id, ts, queued_sha, filename, body
                )
                token = _identity_token(intake_url)
                headers = {
                    "Content-Type": "text/csv",
                    "X-Ngabo-Lab-Id": lab_id,
                    "X-Ngabo-Source-Id": source_id,
                    "X-Ngabo-Timestamp": ts,
                    "X-Ngabo-Content-SHA256": queued_sha,
                    "X-Ngabo-Signature": signature,
                    "X-Ngabo-Filename": filename,
                }
                if token:
                    headers["Authorization"] = f"Bearer {token}"
                req = request.Request(
                    intake_url,
                    data=body,
                    method="POST",
                    headers=headers,
                )
                try:
                    with request.urlopen(req, timeout=180) as response:
                        if 200 <= response.status < 300:
                            self.queue.mark_acknowledged(item["id"], "batch-ack")
                            self.after(0, self.status_var.set, "● Connected")
                            self.after(0, self._log, f"ACKNOWLEDGED {queued_path.name}")
                        else:
                            self.queue.mark_retry(item["id"], f"HTTP {response.status}")
                            self.after(0, self._log, f"RETRYING {queued_path.name}")
                except Exception as exc:  # noqa: BLE001
                    self.queue.mark_retry(item["id"], str(exc))
                    self.after(0, self._log, f"RETRYING {queued_path.name}: {exc}")


def _identity_token(intake_url: str) -> str | None:
    """Return an audience-bound token for the private demo core.

    Local intake needs no token. Cloud Run uses a narrowly scoped demo invoker
    service account and the signed-in gcloud user's impersonation permission.
    """
    configured = os.environ.get("NGABO_ID_TOKEN", "").strip()
    if configured:
        return configured
    parsed = urlsplit(intake_url)
    if parsed.hostname in {"127.0.0.1", "localhost"}:
        return None
    audience = f"{parsed.scheme}://{parsed.netloc}"
    gcloud = shutil.which("gcloud") or shutil.which("gcloud.cmd")
    if gcloud is None:
        raise RuntimeError("gcloud is required to authenticate Ngabo Connect")
    service_account = os.environ.get(
        "NGABO_CONNECT_SERVICE_ACCOUNT", DEFAULT_INVOKER_SERVICE_ACCOUNT
    )
    return subprocess.check_output(
        [
            gcloud,
            "auth",
            "print-identity-token",
            f"--impersonate-service-account={service_account}",
            f"--audiences={audience}",
        ],
        stderr=subprocess.DEVNULL,
        text=True,
        timeout=30,
    ).strip()


if __name__ == "__main__":
    ConnectApp().mainloop()
