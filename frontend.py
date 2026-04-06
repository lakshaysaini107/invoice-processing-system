import html
import io
import json
import mimetypes
import socket
import subprocess
import sys
import time
import webbrowser
import zipfile
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlencode, urlparse

import requests
from requests.exceptions import RequestException
import streamlit as st
import streamlit.components.v1 as components

# Keep this stable across Streamlit reruns so auth state is only reset
# when we intentionally change the session schema/version.
APP_BOOT_MARKER = "frontend-session-v1"


def apply_futuristic_theme():
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500&family=Plus+Jakarta+Sans:wght@400;500;600&display=swap');

        :root {
            --bg: #f0f4ff;
            --white: #ffffff;
            --glass: rgba(255, 255, 255, 0.78);
            --glass2: rgba(255, 255, 255, 0.92);
            --border: rgba(100, 120, 255, 0.10);
            --border2: rgba(100, 120, 255, 0.22);
            --blue: #4361ee;
            --indigo: #7b2ff7;
            --violet: #b041ff;
            --cyan: #0ea5e9;
            --teal: #06d6a0;
            --rose: #f72585;
            --text: #0f172a;
            --text2: #334155;
            --muted: #64748b;
            --light: #94a3b8;
            --sun: #fb7185;
            --mint: #2dd4bf;
            --gold: #f59e0b;
            --sh: 0 10px 30px rgba(67, 97, 238, 0.12);
            --sh-lg: 0 24px 64px rgba(67, 97, 238, 0.18);
            --motion-fast: 0.25s;
        }

        html, body, [data-testid="stAppViewContainer"], [data-testid="stApp"] {
            scroll-behavior: smooth;
        }

        [data-testid="stAppViewContainer"] {
            position: relative;
            overflow-x: hidden;
            background:
                radial-gradient(760px 320px at -10% -8%, rgba(245, 158, 11, 0.16), transparent 65%),
                radial-gradient(640px 290px at 105% 10%, rgba(45, 212, 191, 0.20), transparent 64%),
                radial-gradient(560px 280px at 35% 98%, rgba(251, 113, 133, 0.16), transparent 62%),
                linear-gradient(135deg, #eef2ff, #f8f9ff, #e9eeff);
            background-size: auto, auto, auto, 220% 220%;
            animation: ifBgShift 18s ease-in-out infinite alternate;
        }

        [data-testid="stApp"] {
            animation: ifPageFadeIn 0.7s ease both;
        }

        ::-webkit-scrollbar {
            width: 10px;
            height: 10px;
        }

        ::-webkit-scrollbar-track {
            background: rgba(217, 225, 255, 0.42);
            border-radius: 999px;
        }

        ::-webkit-scrollbar-thumb {
            background: linear-gradient(180deg, rgba(67, 97, 238, 0.55), rgba(123, 47, 247, 0.6));
            border-radius: 999px;
            border: 2px solid rgba(240, 244, 255, 0.95);
        }

        ::-webkit-scrollbar-thumb:hover {
            background: linear-gradient(180deg, rgba(67, 97, 238, 0.8), rgba(123, 47, 247, 0.82));
        }

        .if-live-bg {
            position: fixed;
            inset: 0;
            pointer-events: none;
            z-index: 0;
            overflow: hidden;
        }

        .if-aurora {
            position: absolute;
            border-radius: 999px;
            filter: blur(70px);
            opacity: 0.36;
            mix-blend-mode: multiply;
            will-change: transform;
        }

        .if-aurora.a1 {
            width: 42vmax;
            height: 42vmax;
            left: -10vmax;
            top: -14vmax;
            background: radial-gradient(circle at 30% 30%, rgba(245, 158, 11, 0.75), rgba(245, 158, 11, 0) 70%);
            animation: ifFloatA 20s ease-in-out infinite alternate;
        }

        .if-aurora.a2 {
            width: 36vmax;
            height: 36vmax;
            right: -9vmax;
            top: 12vh;
            background: radial-gradient(circle at 55% 45%, rgba(45, 212, 191, 0.72), rgba(45, 212, 191, 0) 70%);
            animation: ifFloatB 24s ease-in-out infinite alternate;
        }

        .if-aurora.a3 {
            width: 34vmax;
            height: 34vmax;
            left: 22vw;
            bottom: -14vmax;
            background: radial-gradient(circle at 50% 50%, rgba(251, 113, 133, 0.7), rgba(251, 113, 133, 0) 70%);
            animation: ifFloatC 22s ease-in-out infinite alternate;
        }

        .if-aurora.a4 {
            width: 28vmax;
            height: 28vmax;
            left: 46vw;
            top: 16vh;
            background: radial-gradient(circle at 50% 50%, rgba(244, 114, 182, 0.46), rgba(244, 114, 182, 0) 70%);
            animation: ifFloatB 18s ease-in-out infinite alternate-reverse;
        }

        .if-grid-fog {
            position: absolute;
            inset: -8%;
            background-image:
                linear-gradient(rgba(148, 163, 184, 0.12) 1px, transparent 1px),
                linear-gradient(90deg, rgba(148, 163, 184, 0.12) 1px, transparent 1px);
            background-size: 72px 72px;
            mask-image: radial-gradient(circle at 50% 32%, rgba(0, 0, 0, 0.7), transparent 72%);
            opacity: 0.28;
            animation: ifGridDrift 24s linear infinite;
        }

        @keyframes ifFloatA {
            0% { transform: translate3d(0, 0, 0) scale(1); }
            100% { transform: translate3d(9vmax, 6vmax, 0) scale(1.12); }
        }

        @keyframes ifFloatB {
            0% { transform: translate3d(0, 0, 0) scale(1); }
            100% { transform: translate3d(-8vmax, -5vmax, 0) scale(1.1); }
        }

        @keyframes ifFloatC {
            0% { transform: translate3d(0, 0, 0) scale(1); }
            100% { transform: translate3d(5vmax, -7vmax, 0) scale(1.08); }
        }

        @keyframes ifGridDrift {
            0% { transform: translate3d(0, 0, 0); }
            100% { transform: translate3d(-72px, -72px, 0); }
        }

        @keyframes ifBgShift {
            0% { background-position: 0% 0%; }
            100% { background-position: 100% 100%; }
        }

        @keyframes ifPageFadeIn {
            0% {
                opacity: 0;
                transform: translate3d(0, 8px, 0);
            }
            100% {
                opacity: 1;
                transform: translate3d(0, 0, 0);
            }
        }

        @keyframes ifNavDrop {
            0% {
                opacity: 0;
                transform: translate3d(0, -10px, 0);
            }
            100% {
                opacity: 1;
                transform: translate3d(0, 0, 0);
            }
        }

        @keyframes ifCardRise {
            0% {
                opacity: 0;
                transform: translate3d(0, 14px, 0);
            }
            100% {
                opacity: 1;
                transform: translate3d(0, 0, 0);
            }
        }

        @keyframes ifStatusPulse {
            0%, 100% {
                box-shadow: 0 0 0 0 rgba(6, 214, 160, 0.18);
            }
            50% {
                box-shadow: 0 0 0 8px rgba(6, 214, 160, 0);
            }
        }

        @keyframes ifDotPulse {
            0%, 100% {
                opacity: 0.72;
                transform: scale(0.92);
            }
            50% {
                opacity: 1;
                transform: scale(1.08);
            }
        }

        @keyframes ifLogoOrbit {
            0%, 100% {
                transform: rotate(-2deg) translateY(0);
            }
            50% {
                transform: rotate(2deg) translateY(-2px);
            }
        }

        @keyframes ifHeroFloat {
            0%, 100% {
                transform: translate3d(0, -6px, 0);
            }
            50% {
                transform: translate3d(0, 6px, 0);
            }
        }

        @keyframes ifBadgeWave {
            0%, 100% {
                transform: translateY(0);
            }
            50% {
                transform: translateY(-2px);
            }
        }

        @keyframes ifGradientFlow {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }

        @keyframes ifBorderFlow {
            0% { background-position: 0% 50%; }
            100% { background-position: 200% 50%; }
        }

        @keyframes ifSlideInBottom {
            0% {
                opacity: 0;
                transform: translate3d(0, 20px, 0);
            }
            100% {
                opacity: 1;
                transform: translate3d(0, 0, 0);
            }
        }

        @keyframes ifTabSlideX {
            0% {
                opacity: 0;
                transform: translate3d(14px, 0, 0);
            }
            100% {
                opacity: 1;
                transform: translate3d(0, 0, 0);
            }
        }

        @keyframes ifShimmer {
            0% { background-position: 0% 50%; }
            100% { background-position: 200% 50%; }
        }

        @keyframes ifDropPulse {
            0%, 100% {
                box-shadow: 0 0 0 0 rgba(67, 97, 238, 0.18);
            }
            50% {
                box-shadow: 0 0 0 14px rgba(67, 97, 238, 0);
            }
        }

        @keyframes ifRipple {
            0% {
                transform: translate(-50%, -50%) scale(0);
                opacity: 0.55;
            }
            100% {
                transform: translate(-50%, -50%) scale(2.8);
                opacity: 0;
            }
        }

        @keyframes ifDropRipple {
            0% {
                transform: translate(-50%, -50%) scale(0.2);
                opacity: 0.6;
            }
            100% {
                transform: translate(-50%, -50%) scale(2.4);
                opacity: 0;
            }
        }

        @keyframes ifCapDocBob {
            0%, 100% { transform: translateY(0); }
            50% { transform: translateY(-2px); }
        }

        @keyframes ifCapScan {
            0% {
                transform: translateY(0);
                opacity: 0.3;
            }
            50% {
                opacity: 0.95;
            }
            100% {
                transform: translateY(34px);
                opacity: 0.3;
            }
        }

        @keyframes ifCapFileSlide {
            0%, 100% { transform: translateX(0); }
            50% { transform: translateX(3px); }
        }

        @keyframes ifCapProgress {
            0% { transform: scaleX(0.15); }
            70%, 100% { transform: scaleX(1); }
        }

        @keyframes ifCapReviewPulse {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.02); }
        }

        @keyframes ifCapCheckPulse {
            0%, 100% {
                transform: scale(1);
                box-shadow: 0 0 0 0 rgba(34, 197, 94, 0.22);
            }
            50% {
                transform: scale(1.08);
                box-shadow: 0 0 0 7px rgba(34, 197, 94, 0);
            }
        }

        @keyframes ifCapCorePop {
            0%, 100% { transform: scale(1) rotate(0deg); }
            50% { transform: scale(1.06) rotate(3deg); }
        }

        @keyframes ifCapChipFloat {
            0%, 100% { transform: translateY(0); }
            50% { transform: translateY(-4px); }
        }

        @keyframes ifCapChipFloatCenter {
            0%, 100% { transform: translateX(-50%) translateY(0); }
            50% { transform: translateX(-50%) translateY(-4px); }
        }

        @keyframes ifCapBarPulse {
            0%, 100% { transform: scaleY(0.92); }
            50% { transform: scaleY(1.08); }
        }

        @keyframes ifCapShieldPulse {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.07); }
        }

        [data-testid="stHeader"] {
            background: var(--glass2);
            border-bottom: 1px solid var(--border2);
            backdrop-filter: blur(20px);
        }

        [data-testid="stToolbar"],
        [data-testid="collapsedControl"],
        [data-testid="stSidebar"] {
            display: none !important;
        }

        .main .block-container {
            position: relative;
            z-index: 2;
            max-width: 1250px;
            padding-top: 0.8rem;
            padding-left: 1.2rem;
            padding-bottom: 2.2rem;
        }

        .if-side-rail {
            position: fixed;
            top: 0;
            left: 0;
            width: 78px;
            height: 100vh;
            padding: 18px 0;
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 6px;
            background: var(--glass2);
            border-right: 1px solid var(--border2);
            backdrop-filter: blur(28px);
            z-index: 15;
            box-shadow: 3px 0 20px rgba(67, 97, 238, 0.05);
        }

        .if-rail-logo {
            margin-bottom: 16px;
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 6px;
        }

        .if-rail-gem {
            width: 46px;
            height: 46px;
            border-radius: 14px;
            background: linear-gradient(135deg, var(--blue), var(--indigo) 55%, var(--violet));
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 4px 20px rgba(123, 47, 247, 0.45), inset 0 1px 0 rgba(255, 255, 255, 0.2);
            position: relative;
            overflow: hidden;
        }

        .if-rail-gem::after {
            content: "";
            position: absolute;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: linear-gradient(45deg, transparent 30%, rgba(255, 255, 255, 0.18) 50%, transparent 70%);
            animation: ifShimmer 3.5s linear infinite;
        }

        .if-rail-dot {
            width: 6px;
            height: 6px;
            border-radius: 50%;
            background: var(--teal);
            box-shadow: 0 0 8px var(--teal);
            animation: ifDotPulse 2s ease-in-out infinite;
        }

        .if-rail-item {
            width: 50px;
            height: 50px;
            border-radius: 15px;
            border: 1px solid transparent;
            background: transparent;
            color: var(--light);
            font-family: "JetBrains Mono", monospace !important;
            font-size: 11px;
            letter-spacing: 0.06em;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: transform var(--motion-fast) ease, background-color var(--motion-fast) ease, color var(--motion-fast) ease, border-color var(--motion-fast) ease;
            cursor: pointer;
            position: relative;
        }

        .if-rail-item:hover {
            background: rgba(67, 97, 238, 0.08);
            color: var(--blue);
            transform: scale(1.06);
        }

        .if-rail-item.on {
            background: linear-gradient(135deg, rgba(67, 97, 238, 0.14), rgba(123, 47, 247, 0.08));
            color: var(--blue);
            border-color: rgba(67, 97, 238, 0.22);
            box-shadow: 0 4px 14px rgba(67, 97, 238, 0.18);
        }

        .if-rail-sep {
            width: 30px;
            height: 1px;
            background: var(--border2);
            margin: 6px 0;
        }

        .if-rail-bottom {
            margin-top: auto;
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 6px;
        }

        p, label, span, div, input, textarea {
            font-family: "Plus Jakarta Sans", sans-serif !important;
            color: var(--text);
        }

        h1, h2, h3 {
            font-family: "Outfit", sans-serif !important;
            letter-spacing: -0.02em;
            color: var(--text) !important;
        }

        .if-topbar {
            position: relative;
            overflow: hidden;
            border: 1px solid var(--border2);
            border-radius: 18px;
            background: linear-gradient(140deg, rgba(255, 255, 255, 0.76), rgba(245, 248, 255, 0.62));
            backdrop-filter: blur(10px);
            padding: 0.95rem 1.2rem;
            min-height: 70px;
            margin-bottom: 0.9rem;
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 12px;
            box-shadow: 0 8px 24px rgba(67, 97, 238, 0.08);
            animation: ifNavDrop 0.6s ease both;
            will-change: transform, opacity;
            position: sticky;
            top: 0.4rem;
            z-index: 12;
        }

        .if-topbar::before {
            content: "";
            position: absolute;
            inset: 0;
            background: linear-gradient(115deg, rgba(67, 97, 238, 0.08), rgba(123, 47, 247, 0.06) 48%, rgba(14, 165, 233, 0.05));
            pointer-events: none;
        }

        .if-brand {
            display: flex;
            align-items: center;
            gap: 10px;
            position: relative;
            z-index: 1;
        }

        .if-brand-wrap {
            display: flex;
            align-items: center;
            gap: 12px;
            min-width: 0;
        }

        .if-gem {
            width: 44px;
            height: 44px;
            border-radius: 14px;
            background: linear-gradient(135deg, var(--blue), var(--indigo) 55%, var(--violet));
            display: flex;
            align-items: center;
            justify-content: center;
            color: #fff;
            box-shadow: 0 8px 22px rgba(123, 47, 247, 0.35);
            overflow: hidden;
            transition: transform var(--motion-fast) ease, box-shadow var(--motion-fast) ease, filter var(--motion-fast) ease;
            will-change: transform, box-shadow;
            transform: translateZ(0);
        }

        .if-gem:hover {
            transform: translateZ(0) scale(1.05);
            box-shadow: 0 14px 34px rgba(123, 47, 247, 0.44);
            filter: drop-shadow(0 0 8px rgba(80, 130, 255, 0.35));
        }

        .if-gem svg {
            width: 28px;
            height: 28px;
            display: block;
        }

        .if-brand-title {
            font-family: "Outfit", sans-serif !important;
            font-size: 1.08rem;
            font-weight: 800;
            line-height: 1;
            background: linear-gradient(135deg, var(--blue), var(--indigo), var(--violet));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }

        .if-brand-sub {
            font-size: 0.74rem;
            font-family: "JetBrains Mono", monospace !important;
            color: var(--muted) !important;
            margin-top: 2px;
        }

        .if-brand-div {
            width: 1px;
            height: 34px;
            background: var(--border2);
            margin: 0 3px;
        }

        .if-page-tag {
            font-size: 0.8rem;
            color: var(--muted) !important;
            font-weight: 500;
        }

        .if-top-actions {
            display: flex;
            align-items: center;
            gap: 8px;
            position: relative;
            z-index: 1;
            flex-shrink: 0;
        }

        .if-status {
            border: 1px solid rgba(6, 214, 160, 0.35);
            color: #059669 !important;
            background: rgba(6, 214, 160, 0.08);
            border-radius: 999px;
            padding: 0.3rem 0.72rem;
            font-size: 0.72rem;
            font-weight: 700;
            font-family: "JetBrains Mono", monospace !important;
            display: inline-flex;
            align-items: center;
            gap: 0.36rem;
            position: relative;
            z-index: 1;
        }

        .if-status::before {
            content: "";
            width: 8px;
            height: 8px;
            border-radius: 999px;
            background: #22c55e;
            box-shadow: 0 0 0 0 rgba(34, 197, 94, 0.35);
            animation: ifDotPulse 2s ease-in-out infinite, ifStatusPulse 2s ease-in-out infinite;
        }

        .if-icon-btn {
            width: 38px;
            height: 38px;
            border-radius: 12px;
            border: 1px solid var(--border2);
            background: var(--white);
            color: var(--muted);
            font-size: 0.95rem;
            font-family: "JetBrains Mono", monospace !important;
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 2px 10px rgba(67, 97, 238, 0.06);
            transition: transform var(--motion-fast) ease, border-color var(--motion-fast) ease, color var(--motion-fast) ease;
        }

        .if-icon-btn:hover {
            border-color: var(--blue);
            color: var(--blue);
            transform: scale(1.05);
        }

        .if-avatar {
            width: 38px;
            height: 38px;
            border-radius: 12px;
            background: linear-gradient(135deg, var(--blue), var(--indigo));
            color: #fff;
            font-size: 0.72rem;
            font-weight: 700;
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 4px 14px rgba(67, 97, 238, 0.3), inset 0 1px 0 rgba(255, 255, 255, 0.2);
            transition: transform var(--motion-fast) ease;
        }

        .if-avatar:hover {
            transform: scale(1.08);
        }

        .if-user-strip {
            display: flex;
            align-items: center;
            gap: 14px;
            border: 1px solid var(--border2);
            border-radius: 20px;
            background: linear-gradient(145deg, rgba(255, 255, 255, 0.82), rgba(240, 244, 255, 0.68));
            box-shadow: 0 12px 28px rgba(67, 97, 238, 0.10);
            padding: 0.9rem 1rem;
            margin-bottom: 0.9rem;
            animation: ifNavDrop 0.6s ease both;
        }

        .if-user-avatar {
            width: 48px;
            height: 48px;
            border-radius: 16px;
            background: linear-gradient(135deg, var(--blue), var(--indigo) 55%, var(--violet));
            color: #fff !important;
            display: flex;
            align-items: center;
            justify-content: center;
            font-family: "Outfit", sans-serif !important;
            font-size: 1rem;
            font-weight: 800;
            letter-spacing: 0.04em;
            box-shadow: 0 10px 24px rgba(123, 47, 247, 0.28);
            flex-shrink: 0;
        }

        .if-user-copy {
            min-width: 0;
        }

        .if-user-title {
            font-family: "Outfit", sans-serif !important;
            font-size: 1rem;
            font-weight: 800;
            letter-spacing: -0.02em;
            color: var(--text) !important;
        }

        .if-user-meta {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-top: 0.35rem;
        }

        .if-user-chip {
            display: inline-flex;
            align-items: center;
            gap: 0.38rem;
            border-radius: 999px;
            padding: 0.28rem 0.68rem;
            background: rgba(67, 97, 238, 0.08);
            border: 1px solid rgba(67, 97, 238, 0.10);
            color: var(--text2) !important;
            font-size: 0.74rem;
            line-height: 1;
        }

        .if-user-chip.role {
            background: rgba(6, 214, 160, 0.10);
            border-color: rgba(6, 214, 160, 0.18);
            color: #047857 !important;
            font-weight: 700;
        }

        .if-user-chip.presence {
            background: rgba(14, 165, 233, 0.10);
            border-color: rgba(14, 165, 233, 0.16);
            color: #075985 !important;
            font-weight: 700;
        }

        .if-auth-card-marker {
            display: none;
        }

        .main .block-container:has(.if-auth-screen) {
            max-width: 980px;
            min-height: calc(100vh - 2.5rem);
            display: flex;
            flex-direction: column;
            justify-content: center;
            padding-top: 1rem;
            padding-right: 1rem;
            padding-bottom: 1rem;
            padding-left: 1rem;
        }

        .if-auth-screen {
            position: relative;
            text-align: center;
            padding: 0 0 0.8rem;
            margin: 0 auto 0.9rem;
        }

        .if-auth-screen::before {
            content: "";
            position: absolute;
            inset: -1rem 10% auto;
            height: 250px;
            border-radius: 999px;
            background:
                radial-gradient(circle at 50% 18%, rgba(67, 97, 238, 0.16), transparent 38%),
                radial-gradient(circle at 24% 58%, rgba(123, 47, 247, 0.12), transparent 30%),
                radial-gradient(circle at 76% 56%, rgba(14, 165, 233, 0.12), transparent 28%);
            filter: blur(18px);
            pointer-events: none;
            z-index: 0;
        }

        .if-auth-brand {
            position: relative;
            z-index: 1;
            max-width: 100%;
            margin: 0 auto;
            padding: 0.15rem 0 0;
        }

        .if-auth-brand::before {
            content: "";
            position: absolute;
            inset: 1.8rem 10% auto;
            height: 170px;
            border-radius: 26px;
            border: 1px solid rgba(255, 255, 255, 0.52);
            background:
                linear-gradient(180deg, rgba(255, 255, 255, 0.58), rgba(255, 255, 255, 0.14)),
                radial-gradient(circle at top, rgba(67, 97, 238, 0.10), transparent 72%);
            box-shadow: 0 20px 42px rgba(15, 23, 42, 0.05);
            pointer-events: none;
            z-index: 0;
        }

        .if-auth-badge {
            position: relative;
            z-index: 1;
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            margin: 0 auto 0.8rem;
            padding: 0.48rem 0.92rem;
            border-radius: 999px;
            border: 1px solid rgba(99, 102, 241, 0.20);
            background: rgba(255, 255, 255, 0.78);
            color: var(--blue) !important;
            font-size: 0.74rem;
            font-weight: 800;
            letter-spacing: 0.12em;
            text-transform: uppercase;
            box-shadow: 0 12px 24px rgba(148, 163, 184, 0.08);
            animation: ifBadgeWave 6s ease-in-out infinite;
        }

        .if-auth-badge::before {
            content: "";
            width: 10px;
            height: 10px;
            border-radius: 999px;
            background: linear-gradient(135deg, var(--blue), var(--indigo));
            box-shadow: 0 0 0 5px rgba(67, 97, 238, 0.10);
        }

        .if-auth-logo {
            position: relative;
            z-index: 1;
            width: 82px;
            height: 82px;
            margin: 0 auto 0.8rem;
            border-radius: 24px;
            background: linear-gradient(145deg, var(--blue), var(--indigo) 58%, var(--violet));
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow:
                0 18px 42px rgba(67, 97, 238, 0.18),
                0 8px 24px rgba(123, 47, 247, 0.16),
                inset 0 1px 0 rgba(255, 255, 255, 0.24);
            animation: ifLogoOrbit 10s ease-in-out infinite;
        }

        .if-auth-logo::after {
            content: "";
            position: absolute;
            inset: -12px;
            border-radius: 28px;
            background: radial-gradient(circle, rgba(123, 47, 247, 0.16), transparent 70%);
            z-index: -1;
        }

        .if-auth-logo svg {
            width: 54px;
            height: 54px;
            display: block;
        }

        .if-auth-title {
            position: relative;
            z-index: 1;
            font-family: "Outfit", sans-serif !important;
            font-size: clamp(2.55rem, 5vw, 3.6rem);
            font-weight: 900;
            letter-spacing: -0.06em;
            line-height: 0.93;
            margin-bottom: 0.65rem;
            background: linear-gradient(135deg, var(--text) 0%, var(--blue) 36%, var(--indigo) 68%, var(--violet) 100%);
            background-size: 180% 180%;
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            animation: ifGradientFlow 10s ease infinite;
        }

        .if-auth-title span {
            background: linear-gradient(135deg, var(--blue) 10%, var(--indigo) 58%, var(--violet) 100%);
            background-size: 180% 180%;
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            animation: ifGradientFlow 10s ease infinite;
        }

        .if-auth-copy {
            position: relative;
            z-index: 1;
            max-width: 520px;
            margin: 0 auto;
            color: rgba(51, 65, 85, 0.84) !important;
            font-size: 0.97rem;
            line-height: 1.62;
        }

        .if-auth-highlights {
            position: relative;
            z-index: 1;
            display: flex;
            justify-content: center;
            flex-wrap: wrap;
            gap: 0.55rem;
            max-width: 560px;
            margin: 0.85rem auto 0;
        }

        .if-auth-highlight {
            display: inline-flex;
            align-items: center;
            gap: 0.55rem;
            padding: 0.58rem 0.85rem;
            border-radius: 999px;
            border: 1px solid rgba(99, 102, 241, 0.16);
            background: rgba(255, 255, 255, 0.82);
            color: #334155 !important;
            font-size: 0.9rem;
            font-weight: 700;
            box-shadow: 0 10px 18px rgba(148, 163, 184, 0.10);
        }

        .if-auth-highlight::before {
            content: "";
            width: 10px;
            height: 10px;
            border-radius: 999px;
            background: linear-gradient(135deg, var(--blue), var(--indigo));
            box-shadow: 0 0 0 5px rgba(67, 97, 238, 0.10);
        }

        div[data-testid="stVerticalBlock"]:has(.if-auth-card-marker):not(:has(div[data-testid="stVerticalBlock"] .if-auth-card-marker)) {
            position: relative;
            width: 100%;
            max-width: 720px;
            margin: 0 auto;
            padding: 1.5rem;
            border-radius: 24px;
            border: 1px solid rgba(226, 232, 240, 0.92);
            background: linear-gradient(180deg, rgba(255, 255, 255, 0.96), rgba(248, 250, 252, 0.92));
            backdrop-filter: blur(18px);
            box-shadow:
                0 18px 40px rgba(67, 97, 238, 0.12),
                0 8px 18px rgba(123, 47, 247, 0.08);
            overflow: hidden;
        }

        div[data-testid="stVerticalBlock"]:has(.if-auth-card-marker):not(:has(div[data-testid="stVerticalBlock"] .if-auth-card-marker))::before {
            content: "";
            position: absolute;
            inset: 8px;
            border-radius: 18px;
            border: 1px solid rgba(99, 102, 241, 0.12);
            background: linear-gradient(180deg, rgba(255, 255, 255, 0.56), rgba(255, 255, 255, 0));
            pointer-events: none;
        }

        div[data-testid="stVerticalBlock"]:has(.if-auth-card-marker):not(:has(div[data-testid="stVerticalBlock"] .if-auth-card-marker))::after {
            content: "";
            position: absolute;
            left: 16%;
            right: 16%;
            top: 0;
            height: 120px;
            border-radius: 50%;
            background: radial-gradient(circle at 50% 0%, rgba(67, 97, 238, 0.12), rgba(123, 47, 247, 0.08), transparent 72%);
            filter: blur(28px);
            pointer-events: none;
        }

        div[data-testid="stVerticalBlock"]:has(.if-auth-card-marker):not(:has(div[data-testid="stVerticalBlock"] .if-auth-card-marker)) > div {
            position: relative;
            z-index: 1;
        }

        .if-auth-card-head {
            max-width: 460px;
            margin: 0 auto 0.8rem;
            text-align: center;
        }

        .if-auth-card-title {
            color: var(--text2) !important;
            font-family: "Outfit", sans-serif !important;
            font-size: 1.35rem;
            font-weight: 800;
            letter-spacing: -0.04em;
            line-height: 1.1;
            margin-top: 0.2rem;
        }

        div[data-testid="stVerticalBlock"]:has(.if-auth-card-marker):not(:has(div[data-testid="stVerticalBlock"] .if-auth-card-marker)) [data-testid="stAlert"] {
            border-radius: 18px;
            border: 1px solid rgba(99, 102, 241, 0.18);
            background: linear-gradient(180deg, rgba(239, 246, 255, 0.95), rgba(255, 255, 255, 0.84));
            box-shadow: 0 10px 24px rgba(148, 163, 184, 0.10);
            text-align: center;
        }

        div[data-testid="stVerticalBlock"]:has(.if-auth-card-marker):not(:has(div[data-testid="stVerticalBlock"] .if-auth-card-marker)) [data-testid="stTabs"] [role="tablist"],
        div[data-testid="stVerticalBlock"]:has(.if-auth-card-marker):not(:has(div[data-testid="stVerticalBlock"] .if-auth-card-marker)) .stTabs [data-baseweb="tab-list"] {
            width: min(100%, 520px);
            margin: 0 auto 0.95rem;
            gap: 4px;
            border-radius: 18px;
            padding: 5px;
            border: 1px solid rgba(99, 102, 241, 0.18);
            background: linear-gradient(135deg, rgba(238, 242, 255, 0.96), rgba(248, 250, 252, 0.90));
            box-shadow:
                inset 0 1px 0 rgba(255, 255, 255, 0.96),
                0 12px 28px rgba(148, 163, 184, 0.10);
            justify-content: center;
        }

        div[data-testid="stVerticalBlock"]:has(.if-auth-card-marker):not(:has(div[data-testid="stVerticalBlock"] .if-auth-card-marker)) [data-testid="stTabs"] button[role="tab"],
        div[data-testid="stVerticalBlock"]:has(.if-auth-card-marker):not(:has(div[data-testid="stVerticalBlock"] .if-auth-card-marker)) .stTabs [data-baseweb="tab"] {
            min-height: 56px;
            min-width: 160px;
            font-size: 1rem;
            font-weight: 700;
            border-radius: 14px;
            color: rgba(71, 85, 105, 0.95) !important;
            transition: transform 0.2s ease, box-shadow 0.2s ease, color 0.2s ease;
            flex: 1 1 0;
        }

        div[data-testid="stVerticalBlock"]:has(.if-auth-card-marker):not(:has(div[data-testid="stVerticalBlock"] .if-auth-card-marker)) [data-testid="stTabs"] button[role="tab"]::after,
        div[data-testid="stVerticalBlock"]:has(.if-auth-card-marker):not(:has(div[data-testid="stVerticalBlock"] .if-auth-card-marker)) .stTabs [data-baseweb="tab"]::after {
            display: none;
        }

        div[data-testid="stVerticalBlock"]:has(.if-auth-card-marker):not(:has(div[data-testid="stVerticalBlock"] .if-auth-card-marker)) [data-testid="stTabs"] button[role="tab"]:hover,
        div[data-testid="stVerticalBlock"]:has(.if-auth-card-marker):not(:has(div[data-testid="stVerticalBlock"] .if-auth-card-marker)) .stTabs [data-baseweb="tab"]:hover {
            transform: translateY(0);
            background: rgba(255, 255, 255, 0.88);
            color: var(--blue) !important;
            text-shadow: none;
        }

        div[data-testid="stVerticalBlock"]:has(.if-auth-card-marker):not(:has(div[data-testid="stVerticalBlock"] .if-auth-card-marker)) [data-testid="stTabs"] [aria-selected="true"],
        div[data-testid="stVerticalBlock"]:has(.if-auth-card-marker):not(:has(div[data-testid="stVerticalBlock"] .if-auth-card-marker)) .stTabs [aria-selected="true"] {
            color: #fff !important;
            background: linear-gradient(135deg, var(--blue), var(--indigo) 58%, var(--violet));
            box-shadow: 0 12px 24px rgba(123, 47, 247, 0.22);
        }

        div[data-testid="stVerticalBlock"]:has(.if-auth-card-marker):not(:has(div[data-testid="stVerticalBlock"] .if-auth-card-marker)) [data-testid="stTabs"] [role="tabpanel"] {
            max-width: 600px;
            margin: 0 auto;
            padding: 1.05rem 1rem 0.95rem;
            border-radius: 22px;
            border: 1px solid rgba(226, 232, 240, 0.92);
            background: linear-gradient(180deg, rgba(255, 255, 255, 0.92), rgba(238, 242, 255, 0.70));
            box-shadow:
                inset 0 1px 0 rgba(255, 255, 255, 0.92),
                0 16px 36px rgba(148, 163, 184, 0.12);
            text-align: center;
        }

        .if-auth-panel-intro {
            max-width: 430px;
            margin: 0 auto 0.75rem;
            text-align: center;
        }

        .if-auth-panel-kicker {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            margin-bottom: 0.5rem;
            padding: 0.36rem 0.72rem;
            border-radius: 999px;
            border: 1px solid rgba(99, 102, 241, 0.18);
            background: rgba(238, 242, 255, 0.92);
            color: var(--blue) !important;
            font-size: 0.72rem;
            font-weight: 800;
            letter-spacing: 0.12em;
            text-transform: uppercase;
        }

        .if-auth-panel-title {
            color: var(--text2) !important;
            font-family: "Outfit", sans-serif !important;
            font-size: 1.4rem;
            font-weight: 800;
            line-height: 1.1;
            letter-spacing: -0.04em;
        }

        .if-auth-panel-copy {
            margin-top: 0.4rem;
            color: rgba(71, 85, 105, 0.82) !important;
            font-size: 0.9rem;
            line-height: 1.55;
        }

        div[data-testid="stVerticalBlock"]:has(.if-auth-card-marker):not(:has(div[data-testid="stVerticalBlock"] .if-auth-card-marker)) [data-testid="stForm"] {
            max-width: 560px;
            margin: 0 auto;
            background: transparent;
            border: none;
            padding: 0;
            text-align: left;
        }

        div[data-testid="stVerticalBlock"]:has(.if-auth-card-marker):not(:has(div[data-testid="stVerticalBlock"] .if-auth-card-marker)) [data-testid="stTextInput"] {
            margin-bottom: 0.7rem;
        }

        div[data-testid="stVerticalBlock"]:has(.if-auth-card-marker):not(:has(div[data-testid="stVerticalBlock"] .if-auth-card-marker)) .stTextInput input {
            min-height: 56px;
            border-radius: 16px !important;
            border: 1px solid rgba(203, 213, 225, 0.9) !important;
            background: linear-gradient(180deg, rgba(255, 255, 255, 0.98), rgba(248, 250, 252, 0.94)) !important;
            box-shadow:
                inset 0 1px 0 rgba(255, 255, 255, 0.92),
                0 10px 22px rgba(148, 163, 184, 0.10);
            font-size: 1rem;
            padding-left: 1rem !important;
            color: #0f172a !important;
        }

        div[data-testid="stVerticalBlock"]:has(.if-auth-card-marker):not(:has(div[data-testid="stVerticalBlock"] .if-auth-card-marker)) .stTextInput input::placeholder {
            color: rgba(100, 116, 139, 0.72) !important;
        }

        div[data-testid="stVerticalBlock"]:has(.if-auth-card-marker):not(:has(div[data-testid="stVerticalBlock"] .if-auth-card-marker)) .stTextInput input:focus {
            border-color: rgba(67, 97, 238, 0.56) !important;
            box-shadow:
                0 0 0 4px rgba(67, 97, 238, 0.14),
                0 14px 28px rgba(123, 47, 247, 0.10) !important;
        }

        div[data-testid="stVerticalBlock"]:has(.if-auth-card-marker):not(:has(div[data-testid="stVerticalBlock"] .if-auth-card-marker)) .stButton > button,
        div[data-testid="stVerticalBlock"]:has(.if-auth-card-marker):not(:has(div[data-testid="stVerticalBlock"] .if-auth-card-marker)) .stFormSubmitButton > button {
            min-height: 58px;
            border-radius: 18px;
            border: none !important;
            font-size: 1.08rem;
            font-family: "Outfit", sans-serif !important;
            font-weight: 800;
            letter-spacing: -0.01em;
            color: #fff !important;
            background: linear-gradient(135deg, var(--blue), var(--indigo) 54%, var(--violet)) !important;
            box-shadow:
                0 18px 34px rgba(123, 47, 247, 0.24),
                inset 0 1px 0 rgba(255, 255, 255, 0.18);
        }

        div[data-testid="stVerticalBlock"]:has(.if-auth-card-marker):not(:has(div[data-testid="stVerticalBlock"] .if-auth-card-marker)) .stButton > button:hover,
        div[data-testid="stVerticalBlock"]:has(.if-auth-card-marker):not(:has(div[data-testid="stVerticalBlock"] .if-auth-card-marker)) .stFormSubmitButton > button:hover {
            transform: translateY(-1px);
            box-shadow: 0 22px 42px rgba(123, 47, 247, 0.28);
        }

        .if-auth-footer {
            text-align: center;
            max-width: 100%;
            margin: 0.85rem auto 0;
            padding-top: 0.8rem;
            padding-bottom: 0.2rem;
            border-top: 1px solid rgba(99, 102, 241, 0.10);
        }

        .if-auth-footer-copy {
            color: rgba(51, 65, 85, 0.86) !important;
            font-size: 0.93rem;
            line-height: 1.6;
        }

        .if-auth-divider {
            width: min(520px, 82%);
            height: 1px;
            margin: 0.75rem auto 0.7rem;
            background: linear-gradient(90deg, rgba(148, 163, 184, 0), rgba(148, 163, 184, 0.34), rgba(148, 163, 184, 0));
        }

        .if-auth-footer-note {
            color: rgba(100, 116, 139, 0.84) !important;
            font-size: 0.84rem;
        }

        .if-hero {
            border: 1px solid var(--border2);
            border-radius: 22px;
            background: linear-gradient(160deg, rgba(255, 255, 255, 0.72), rgba(240, 244, 255, 0.48));
            text-align: center;
            padding: 2.4rem 1rem 1.7rem;
            margin-bottom: 1rem;
            box-shadow: var(--sh);
            animation: ifCardRise 0.75s ease both;
            will-change: transform, opacity;
            position: relative;
            overflow: hidden;
        }

        .if-hero::before {
            content: "";
            position: absolute;
            inset: 0;
            background: radial-gradient(ellipse 80% 120% at 50% 0%, rgba(67, 97, 238, 0.08), transparent 66%);
            pointer-events: none;
        }

        .if-hero-rings {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            width: 320px;
            height: 320px;
            pointer-events: none;
            z-index: 0;
        }

        .if-hero-ring {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            border-radius: 50%;
            border: 1px solid rgba(67, 97, 238, 0.12);
        }

        .if-hero-ring:nth-child(1) {
            width: 140px;
            height: 140px;
            animation: ifLogoOrbit 12s linear infinite;
        }

        .if-hero-ring:nth-child(2) {
            width: 210px;
            height: 210px;
            border-style: dashed;
            animation: ifLogoOrbit 20s linear infinite reverse;
        }

        .if-hero-ring:nth-child(3) {
            width: 300px;
            height: 300px;
            border-color: rgba(123, 47, 247, 0.08);
            animation: ifLogoOrbit 30s linear infinite;
        }

        .if-hero-logo-wrap {
            position: relative;
            z-index: 1;
            margin-bottom: 0.25rem;
        }

        .if-hero-gem {
            width: 90px;
            height: 90px;
            border-radius: 24px;
            margin: 0 auto 0.8rem;
            background: linear-gradient(135deg, var(--blue), var(--indigo) 50%, var(--violet));
            display: flex;
            align-items: center;
            justify-content: center;
            color: #fff;
            box-shadow: 0 16px 42px rgba(123, 47, 247, 0.35);
            animation: ifHeroFloat 5.8s ease-in-out infinite;
        }

        .if-hero-gem svg {
            width: 56px;
            height: 56px;
            display: block;
        }

        .if-hero-title {
            font-family: "Outfit", sans-serif !important;
            font-size: clamp(2rem, 4vw, 2.8rem);
            font-weight: 900;
            letter-spacing: -0.04em;
            line-height: 1.02;
            background: linear-gradient(135deg, var(--blue), var(--indigo), var(--violet), var(--rose));
            background-size: 220% 220%;
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            animation: ifCardRise 0.9s ease both, ifGradientFlow 7.8s ease infinite;
        }

        .if-hero-sub {
            max-width: 760px;
            margin: 0.5rem auto 0;
            color: var(--muted) !important;
            font-size: 0.96rem;
            position: relative;
            z-index: 1;
        }

        .if-badge-row {
            display: flex;
            justify-content: center;
            flex-wrap: wrap;
            gap: 8px;
            margin-top: 0.95rem;
        }

        .if-badge {
            border: 1px solid var(--border2);
            background: var(--white);
            border-radius: 999px;
            padding: 0.25rem 0.72rem;
            font-size: 0.73rem;
            color: var(--text2) !important;
            box-shadow: 0 2px 10px rgba(67, 97, 238, 0.09);
            transition: transform var(--motion-fast) ease, box-shadow var(--motion-fast) ease, background var(--motion-fast) ease;
            animation: ifBadgeWave 5.5s ease-in-out infinite;
            will-change: transform, box-shadow;
            display: inline-flex;
            align-items: center;
            gap: 7px;
            position: relative;
            z-index: 1;
        }

        .if-badge:hover {
            transform: translateY(-2px) scale(1.05);
            box-shadow: 0 12px 26px rgba(67, 97, 238, 0.24);
            background: linear-gradient(135deg, rgba(67, 97, 238, 0.16), rgba(123, 47, 247, 0.13));
        }

        .if-badge-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
        }

        .if-badge-dot.d1 { background: var(--blue); box-shadow: 0 0 8px var(--blue); }
        .if-badge-dot.d2 { background: var(--teal); box-shadow: 0 0 8px var(--teal); }
        .if-badge-dot.d3 { background: var(--rose); box-shadow: 0 0 8px var(--rose); }
        .if-badge-dot.d4 { background: var(--indigo); box-shadow: 0 0 8px var(--indigo); }
        .if-badge-dot.d5 { background: var(--cyan); box-shadow: 0 0 8px var(--cyan); }

        .if-cap-head {
            display: flex;
            align-items: center;
            gap: 12px;
            margin: 0.2rem 0 0.65rem;
        }

        .if-cap-title {
            font-family: "Outfit", sans-serif !important;
            font-weight: 800;
            font-size: 1.2rem;
            letter-spacing: -0.02em;
            color: var(--text) !important;
        }

        .if-cap-title b {
            color: var(--blue) !important;
        }

        .if-cap-sub {
            color: var(--muted) !important;
            font-size: 0.82rem;
        }

        .if-cap-grid {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 12px;
            margin-bottom: 0.95rem;
        }

        .if-cap-card {
            position: relative;
            overflow: hidden;
            border: 1px solid var(--border2);
            border-radius: 22px;
            background: var(--glass);
            box-shadow: var(--sh);
            transition: transform var(--motion-fast) ease, box-shadow var(--motion-fast) ease, border-color var(--motion-fast) ease;
            opacity: 0;
            transform: translate3d(0, 16px, 0);
            animation: ifSlideInBottom 0.58s ease forwards;
            will-change: transform, box-shadow, opacity;
        }

        .if-cap-card::before {
            content: "";
            position: absolute;
            inset: 0;
            border-radius: inherit;
            padding: 1px;
            background: linear-gradient(130deg, rgba(67, 97, 238, 0.58), rgba(123, 47, 247, 0.52), rgba(14, 165, 233, 0.54));
            background-size: 200% 100%;
            opacity: 0;
            pointer-events: none;
            -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
            -webkit-mask-composite: xor;
            mask-composite: exclude;
            transition: opacity var(--motion-fast) ease;
        }

        .if-cap-card:nth-child(1) { animation-delay: 0.1s; }
        .if-cap-card:nth-child(2) { animation-delay: 0.2s; }
        .if-cap-card:nth-child(3) { animation-delay: 0.3s; }
        .if-cap-card:nth-child(4) { animation-delay: 0.4s; }
        .if-cap-card:nth-child(5) { animation-delay: 0.5s; }
        .if-cap-card:nth-child(6) { animation-delay: 0.6s; }

        .if-cap-card:hover::before {
            opacity: 1;
            animation: ifBorderFlow 2.2s linear infinite;
        }

        .if-cap-card:hover {
            transform: translateY(-6px);
            box-shadow: 0 22px 42px rgba(67, 97, 238, 0.2);
        }

        .if-cap-visual {
            height: 132px;
            position: relative;
            overflow: hidden;
            display: flex;
            align-items: stretch;
            justify-content: stretch;
            border-bottom: 1px solid var(--border);
            padding: 12px 14px;
        }

        .if-cap-visual.v1 { background: linear-gradient(135deg, #eef2ff, #e0e7ff); }
        .if-cap-visual.v2 { background: linear-gradient(135deg, #f0fdf4, #dcfce7); }
        .if-cap-visual.v3 { background: linear-gradient(135deg, #fff7ed, #ffedd5); }
        .if-cap-visual.v4 { background: linear-gradient(135deg, #fdf4ff, #fae8ff); }
        .if-cap-visual.v5 { background: linear-gradient(135deg, #ecfeff, #cffafe); }
        .if-cap-visual.v6 { background: linear-gradient(135deg, #fff1f2, #ffe4e6); }

        .if-cap-label {
            position: absolute;
            right: 10px;
            top: 8px;
            font-family: "JetBrains Mono", monospace !important;
            font-size: 0.58rem;
            letter-spacing: 0.06em;
            color: var(--muted);
            opacity: 0.92;
        }

        .cap-ocr-wrap,
        .cap-batch-list,
        .cap-review-card,
        .cap-export-scene,
        .cap-live-chart,
        .cap-sec-scene {
            width: 100%;
            height: 100%;
            position: relative;
            z-index: 1;
        }

        .cap-ocr-wrap {
            display: flex;
            flex-direction: column;
            justify-content: center;
            gap: 7px;
        }

        .cap-ocr-doc {
            position: relative;
            border-radius: 10px;
            background: rgba(255, 255, 255, 0.9);
            border: 1px solid rgba(99, 102, 241, 0.2);
            padding: 10px 10px 8px;
            box-shadow: 0 8px 14px rgba(67, 97, 238, 0.12);
            animation: ifCapDocBob 3s ease-in-out infinite;
        }

        .cap-ocr-scan {
            position: absolute;
            left: 10px;
            right: 10px;
            top: 10px;
            height: 2px;
            border-radius: 999px;
            background: linear-gradient(90deg, rgba(67, 97, 238, 0), rgba(67, 97, 238, 0.9), rgba(67, 97, 238, 0));
            animation: ifCapScan 2.5s ease-in-out infinite;
        }

        .cap-ocr-line {
            height: 6px;
            border-radius: 4px;
            background: linear-gradient(90deg, #e0e7ff, #c7d2fe);
            margin-bottom: 4px;
        }

        .cap-ocr-line.w1 { width: 88%; }
        .cap-ocr-line.w2 { width: 60%; }
        .cap-ocr-line.w3 { width: 94%; }
        .cap-ocr-line.w4 { width: 54%; margin-bottom: 0; }

        .cap-ocr-tags {
            display: flex;
            gap: 6px;
            flex-wrap: wrap;
        }

        .cap-pill {
            font-family: "JetBrains Mono", monospace !important;
            font-size: 0.55rem;
            line-height: 1;
            padding: 4px 8px;
            border-radius: 999px;
            border: 1px solid rgba(67, 97, 238, 0.2);
            background: rgba(255, 255, 255, 0.78);
            color: var(--text2);
        }

        .cap-batch-list {
            display: flex;
            flex-direction: column;
            justify-content: center;
            gap: 7px;
        }

        .cap-batch-item {
            display: grid;
            grid-template-columns: 22px 1fr;
            align-items: center;
            gap: 8px;
            border-radius: 9px;
            border: 1px solid rgba(6, 182, 212, 0.25);
            background: rgba(255, 255, 255, 0.88);
            padding: 7px 8px;
            animation: ifCapFileSlide 2.3s ease-in-out infinite;
        }

        .cap-batch-item:nth-child(2) { animation-delay: 0.18s; }
        .cap-batch-item:nth-child(3) { animation-delay: 0.36s; }

        .cap-batch-dot {
            width: 16px;
            height: 16px;
            border-radius: 6px;
            background: linear-gradient(135deg, rgba(6, 214, 160, 0.25), rgba(14, 165, 233, 0.3));
        }

        .cap-batch-bar {
            height: 5px;
            border-radius: 999px;
            background: rgba(103, 232, 249, 0.28);
            overflow: hidden;
        }

        .cap-batch-fill {
            height: 100%;
            border-radius: inherit;
            transform-origin: left center;
            background: linear-gradient(90deg, #06d6a0, #0ea5e9);
            animation: ifCapProgress 2.1s ease-in-out infinite;
        }

        .cap-batch-item:nth-child(1) .cap-batch-fill { animation-delay: 0s; }
        .cap-batch-item:nth-child(2) .cap-batch-fill { animation-delay: 0.2s; }
        .cap-batch-item:nth-child(3) .cap-batch-fill { animation-delay: 0.4s; }

        .cap-review-card {
            max-width: 190px;
            margin: 0 auto;
            border-radius: 11px;
            border: 1px solid rgba(245, 158, 11, 0.24);
            background: rgba(255, 255, 255, 0.9);
            box-shadow: 0 8px 14px rgba(245, 158, 11, 0.13);
            display: flex;
            flex-direction: column;
            justify-content: center;
            gap: 7px;
            padding: 10px;
            animation: ifCapReviewPulse 2.9s ease-in-out infinite;
        }

        .cap-review-row {
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .cap-review-line {
            flex: 1;
            height: 6px;
            border-radius: 4px;
            background: linear-gradient(90deg, #fdba74, #f59e0b);
            opacity: 0.75;
            transform-origin: left center;
        }

        .cap-review-line.r2 { opacity: 0.62; transform: scaleX(0.78); }
        .cap-review-line.r3 { opacity: 0.54; transform: scaleX(0.62); }

        .cap-review-check {
            width: 14px;
            height: 14px;
            border-radius: 4px;
            background: rgba(34, 197, 94, 0.2);
            border: 1px solid rgba(34, 197, 94, 0.45);
            position: relative;
            animation: ifCapCheckPulse 2.2s ease-in-out infinite;
        }

        .cap-review-check::after {
            content: "";
            position: absolute;
            left: 3px;
            top: 3px;
            width: 6px;
            height: 3px;
            border-left: 2px solid #16a34a;
            border-bottom: 2px solid #16a34a;
            transform: rotate(-45deg);
        }

        .cap-export-scene {
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .cap-export-core {
            width: 52px;
            height: 52px;
            border-radius: 16px;
            background: linear-gradient(135deg, rgba(123, 47, 247, 0.18), rgba(176, 65, 255, 0.14));
            border: 1px solid rgba(123, 47, 247, 0.25);
            box-shadow: 0 6px 18px rgba(123, 47, 247, 0.2);
            display: flex;
            align-items: center;
            justify-content: center;
            font-family: "JetBrains Mono", monospace !important;
            font-size: 0.62rem;
            color: #6d28d9;
            letter-spacing: 0.05em;
            animation: ifCapCorePop 2.4s ease-in-out infinite;
        }

        .cap-export-chip {
            position: absolute;
            padding: 4px 8px;
            border-radius: 8px;
            border: 1px solid rgba(139, 92, 246, 0.2);
            background: rgba(255, 255, 255, 0.86);
            font-family: "JetBrains Mono", monospace !important;
            font-size: 0.54rem;
            color: #6d28d9;
            animation: ifCapChipFloat 2.6s ease-in-out infinite;
        }

        .cap-export-chip.c1 { left: 18px; top: 22px; animation-delay: 0s; }
        .cap-export-chip.c2 { right: 16px; top: 20px; animation-delay: 0.25s; }
        .cap-export-chip.c3 {
            left: 50%;
            bottom: 12px;
            transform: translateX(-50%);
            animation: ifCapChipFloatCenter 2.6s ease-in-out infinite;
            animation-delay: 0.5s;
        }

        .cap-live-chart {
            display: flex;
            flex-direction: column;
            justify-content: center;
            gap: 8px;
        }

        .cap-live-bars {
            height: 58px;
            display: flex;
            align-items: flex-end;
            gap: 6px;
        }

        .cap-live-bar {
            flex: 1;
            border-radius: 5px 5px 2px 2px;
            min-width: 0;
            background: linear-gradient(to top, #67e8f9, #0ea5e9);
            transform-origin: bottom center;
            animation: ifCapBarPulse 2.1s ease-in-out infinite;
        }

        .cap-live-bar.b1 { height: 45%; animation-delay: 0s; }
        .cap-live-bar.b2 { height: 70%; animation-delay: 0.12s; }
        .cap-live-bar.b3 { height: 54%; animation-delay: 0.24s; }
        .cap-live-bar.b4 { height: 86%; animation-delay: 0.36s; }
        .cap-live-bar.b5 { height: 62%; animation-delay: 0.48s; }
        .cap-live-bar.b6 { height: 90%; animation-delay: 0.6s; }

        .cap-live-spark {
            height: 3px;
            border-radius: 999px;
            background: linear-gradient(90deg, rgba(14, 165, 233, 0.1), rgba(14, 165, 233, 0.8), rgba(14, 165, 233, 0.1));
            background-size: 200% 100%;
            animation: ifShimmer 2s linear infinite;
        }

        .cap-sec-scene {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            gap: 10px;
        }

        .cap-sec-shield {
            width: 54px;
            height: 58px;
            background: linear-gradient(160deg, #f72585, #fb7185);
            clip-path: polygon(50% 0%, 92% 18%, 86% 74%, 50% 100%, 14% 74%, 8% 18%);
            position: relative;
            box-shadow: 0 8px 18px rgba(247, 37, 133, 0.3);
            animation: ifCapShieldPulse 2.4s ease-in-out infinite;
        }

        .cap-sec-lock {
            position: absolute;
            left: 50%;
            top: 50%;
            transform: translate(-50%, -50%);
            width: 15px;
            height: 12px;
            border-radius: 3px;
            background: rgba(255, 255, 255, 0.9);
        }

        .cap-sec-lock::before {
            content: "";
            position: absolute;
            left: 3px;
            top: -6px;
            width: 9px;
            height: 8px;
            border: 2px solid rgba(255, 255, 255, 0.9);
            border-bottom: none;
            border-radius: 7px 7px 0 0;
        }

        .cap-sec-bars {
            width: 88%;
            display: flex;
            gap: 5px;
        }

        .cap-sec-bar {
            flex: 1;
            height: 6px;
            border-radius: 4px;
            background: rgba(247, 37, 133, 0.15);
            overflow: hidden;
        }

        .cap-sec-fill {
            height: 100%;
            border-radius: inherit;
            background: linear-gradient(90deg, #f72585, #fb7185);
            transform-origin: left center;
            animation: ifCapProgress 2.3s ease-in-out infinite;
        }

        .cap-sec-bar:nth-child(2) .cap-sec-fill { animation-delay: 0.2s; }
        .cap-sec-bar:nth-child(3) .cap-sec-fill { animation-delay: 0.4s; }

        .if-cap-card:hover .cap-ocr-scan,
        .if-cap-card:hover .cap-batch-fill,
        .if-cap-card:hover .cap-live-bar,
        .if-cap-card:hover .cap-sec-fill {
            animation-duration: 1.6s;
        }

        .if-cap-body {
            padding: 16px 18px 18px;
        }

        .if-cap-icon {
            width: 34px;
            height: 34px;
            border-radius: 10px;
            background: linear-gradient(135deg, rgba(67, 97, 238, 0.14), rgba(123, 47, 247, 0.10));
            display: flex;
            align-items: center;
            justify-content: center;
            margin-bottom: 0.45rem;
            transition: transform var(--motion-fast) ease, box-shadow var(--motion-fast) ease, background var(--motion-fast) ease;
            will-change: transform;
        }

        .if-cap-card:hover .if-cap-icon {
            transform: rotate(6deg) scale(1.08);
            background: linear-gradient(135deg, rgba(67, 97, 238, 0.24), rgba(123, 47, 247, 0.2));
            box-shadow: 0 12px 24px rgba(123, 47, 247, 0.24);
        }

        .if-cap-name {
            font-family: "Outfit", sans-serif !important;
            font-weight: 700;
            font-size: 0.92rem;
            color: var(--text) !important;
        }

        .if-cap-desc {
            font-size: 0.78rem;
            color: var(--muted) !important;
            line-height: 1.45;
            margin-top: 0.15rem;
        }

        .dash-panel {
            border: 1px solid var(--border2);
            border-radius: 18px;
            background: var(--glass);
            padding: 16px;
            margin: 0.2rem 0 1rem;
            backdrop-filter: blur(20px);
            box-shadow: var(--sh);
            animation: ifSlideInBottom 0.62s ease both;
            will-change: transform, opacity;
            transition: transform var(--motion-fast) ease, box-shadow var(--motion-fast) ease, border-color var(--motion-fast) ease;
        }

        .dash-panel:hover {
            transform: translateY(-2px);
            border-color: rgba(67, 97, 238, 0.3);
            box-shadow: 0 20px 34px rgba(67, 97, 238, 0.14);
        }

        .dash-head {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 10px;
        }

        .dash-title {
            font-family: "Outfit", sans-serif !important;
            font-weight: 800;
            color: var(--text) !important;
            letter-spacing: -0.02em;
        }

        .status-pill {
            border-radius: 999px;
            padding: 4px 10px;
            font-size: 0.7rem;
            font-family: "JetBrains Mono", monospace !important;
            font-weight: 700;
            border: 1px solid var(--border2);
            color: var(--text2) !important;
            background: #f8fbff;
            position: relative;
            display: inline-flex;
            align-items: center;
            gap: 6px;
        }

        .status-pill::before {
            content: "";
            width: 7px;
            height: 7px;
            border-radius: 50%;
            background: #22c55e;
            animation: ifDotPulse 2s ease-in-out infinite;
        }

        .status-pill.status-bad::before {
            background: #ef4444;
        }

        .status-pill.status-ok {
            color: #047857 !important;
            background: rgba(16, 185, 129, 0.1);
            border-color: rgba(16, 185, 129, 0.35);
        }

        .status-pill.status-bad {
            color: #b91c1c !important;
            background: rgba(239, 68, 68, 0.1);
            border-color: rgba(239, 68, 68, 0.35);
        }

        .dash-panel-grid {
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 10px;
            margin-top: 10px;
        }

        .dash-metric {
            border: 1px solid var(--border2);
            border-radius: 12px;
            background: rgba(255, 255, 255, 0.88);
            padding: 10px 12px;
            transition: transform var(--motion-fast) ease, box-shadow var(--motion-fast) ease, border-color var(--motion-fast) ease;
            will-change: transform, box-shadow;
            animation: ifSlideInBottom 0.52s ease both;
        }

        .dash-panel-grid .dash-metric:nth-child(1) { animation-delay: 0.1s; }
        .dash-panel-grid .dash-metric:nth-child(2) { animation-delay: 0.2s; }
        .dash-panel-grid .dash-metric:nth-child(3) { animation-delay: 0.3s; }
        .dash-panel-grid .dash-metric:nth-child(4) { animation-delay: 0.4s; }

        .dash-metric.dash-metric-health {
            border-color: rgba(16, 185, 129, 0.3);
        }

        .dash-metric:hover {
            transform: translateY(-4px);
            border-color: rgba(67, 97, 238, 0.34);
            box-shadow: 0 16px 28px rgba(67, 97, 238, 0.2);
        }

        .dash-label {
            color: var(--muted) !important;
            font-size: 0.68rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            font-family: "JetBrains Mono", monospace !important;
        }

        .dash-value {
            color: var(--text) !important;
            font-size: 1rem;
            margin-top: 0.2rem;
            font-weight: 800;
            word-break: break-word;
        }

        .dash-live {
            margin-top: 0.3rem;
            display: inline-flex;
            align-items: center;
            gap: 0.36rem;
            color: #059669 !important;
            font-size: 0.66rem;
            font-family: "JetBrains Mono", monospace !important;
        }

        .dash-live-dot {
            width: 7px;
            height: 7px;
            border-radius: 50%;
            background: #22c55e;
            box-shadow: 0 0 0 0 rgba(34, 197, 94, 0.35);
            animation: ifDotPulse 2s ease-in-out infinite, ifStatusPulse 2s ease-in-out infinite;
        }

        .dash-health-meter {
            margin-top: 11px;
        }

        .dash-health-track {
            width: 100%;
            height: 7px;
            border-radius: 999px;
            background: rgba(148, 163, 184, 0.24);
            overflow: hidden;
            border: 1px solid rgba(99, 102, 241, 0.18);
        }

        .dash-health-fill {
            height: 100%;
            width: var(--health-target, 0%);
            border-radius: inherit;
            background: linear-gradient(90deg, rgba(67, 97, 238, 0.95), rgba(123, 47, 247, 0.95), rgba(6, 214, 160, 0.92));
            background-size: 200% 100%;
            animation: ifShimmer 2.8s linear infinite;
            transform-origin: left center;
            transition: width 0.6s ease;
        }

        .section-head {
            margin: 0.2rem 0 0.75rem;
            padding: 0.8rem 0.9rem;
            border-radius: 14px;
            border: 1px solid var(--border2);
            background: var(--glass);
            box-shadow: var(--sh);
            transition: transform var(--motion-fast) ease, box-shadow var(--motion-fast) ease;
        }

        .section-head:hover {
            transform: translateY(-2px);
            box-shadow: 0 16px 28px rgba(67, 97, 238, 0.14);
        }

        .section-title {
            font-family: "Outfit", sans-serif !important;
            font-weight: 800;
            color: var(--text) !important;
            font-size: 1.02rem;
            letter-spacing: -0.01em;
        }

        .section-sub {
            color: var(--muted) !important;
            font-size: 0.84rem;
            margin-top: 2px;
        }

        .if-upload-shell, .if-recent-shell {
            border: 1px solid var(--border2);
            border-radius: 18px;
            background: var(--glass);
            box-shadow: var(--sh);
            transition: transform var(--motion-fast) ease, box-shadow var(--motion-fast) ease, border-color var(--motion-fast) ease;
            will-change: transform;
        }

        .if-upload-shell:hover, .if-recent-shell:hover {
            transform: translateY(-3px);
            border-color: rgba(67, 97, 238, 0.28);
            box-shadow: 0 18px 30px rgba(67, 97, 238, 0.16);
        }

        .if-upload-head, .if-recent-head {
            padding: 0.95rem 1rem;
            border-bottom: 1px solid var(--border);
            background: rgba(255, 255, 255, 0.56);
        }

        .if-upload-title, .if-recent-title {
            font-family: "Outfit", sans-serif !important;
            font-size: 0.95rem;
            font-weight: 700;
            color: var(--text) !important;
        }

        .if-upload-sub, .if-recent-sub {
            font-size: 0.77rem;
            color: var(--muted) !important;
            margin-top: 2px;
        }

        .if-upload-body, .if-recent-body {
            padding: 1rem;
        }

        .if-recent-grid {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 8px;
            margin-bottom: 10px;
        }

        .if-mini {
            border: 1px solid var(--border);
            border-radius: 10px;
            background: rgba(255, 255, 255, 0.75);
            padding: 8px;
            text-align: center;
            transition: transform var(--motion-fast) ease, box-shadow var(--motion-fast) ease, border-color var(--motion-fast) ease;
            animation: ifSlideInBottom 0.52s ease both;
        }

        .if-mini:nth-child(1) { animation-delay: 0.1s; }
        .if-mini:nth-child(2) { animation-delay: 0.2s; }
        .if-mini:nth-child(3) { animation-delay: 0.3s; }

        .if-mini.if-mini-done {
            border-color: rgba(16, 185, 129, 0.34);
            box-shadow: 0 0 0 1px rgba(16, 185, 129, 0.08), 0 8px 18px rgba(16, 185, 129, 0.12);
        }

        .if-mini.if-mini-running {
            border-color: rgba(245, 158, 11, 0.34);
            box-shadow: 0 0 0 1px rgba(245, 158, 11, 0.08), 0 8px 18px rgba(245, 158, 11, 0.12);
        }

        .if-mini.if-mini-failed {
            border-color: rgba(239, 68, 68, 0.34);
            box-shadow: 0 0 0 1px rgba(239, 68, 68, 0.08), 0 8px 18px rgba(239, 68, 68, 0.12);
        }

        .if-mini:hover {
            transform: translateY(-3px);
            box-shadow: 0 14px 24px rgba(67, 97, 238, 0.18);
        }

        .if-mini-val {
            font-family: "Outfit", sans-serif !important;
            font-size: 1rem;
            font-weight: 800;
            color: var(--text) !important;
        }

        .if-mini-lbl {
            color: var(--light) !important;
            font-size: 0.62rem;
            letter-spacing: 0.08em;
            font-family: "JetBrains Mono", monospace !important;
        }

        .if-recent-item {
            border: 1px solid var(--border);
            border-radius: 11px;
            background: rgba(255, 255, 255, 0.78);
            padding: 7px 9px;
            margin-bottom: 7px;
            transition: transform var(--motion-fast) ease, border-color var(--motion-fast) ease, box-shadow var(--motion-fast) ease;
            animation: ifSlideInBottom 0.45s ease both;
        }

        .if-recent-item:nth-child(1) { animation-delay: 0.08s; }
        .if-recent-item:nth-child(2) { animation-delay: 0.16s; }
        .if-recent-item:nth-child(3) { animation-delay: 0.24s; }
        .if-recent-item:nth-child(4) { animation-delay: 0.32s; }
        .if-recent-item:nth-child(5) { animation-delay: 0.40s; }
        .if-recent-item:nth-child(6) { animation-delay: 0.48s; }
        .if-recent-item:nth-child(7) { animation-delay: 0.56s; }
        .if-recent-item:nth-child(8) { animation-delay: 0.64s; }
        .if-recent-item:nth-child(9) { animation-delay: 0.72s; }
        .if-recent-item:nth-child(10) { animation-delay: 0.80s; }

        .if-recent-state.state-done {
            color: #059669 !important;
            border-color: rgba(16, 185, 129, 0.36);
            background: rgba(16, 185, 129, 0.1);
            box-shadow: 0 0 14px rgba(16, 185, 129, 0.24);
        }

        .if-recent-state.state-running {
            color: #b45309 !important;
            border-color: rgba(245, 158, 11, 0.4);
            background: rgba(245, 158, 11, 0.12);
            box-shadow: 0 0 14px rgba(245, 158, 11, 0.22);
        }

        .if-recent-state.state-failed {
            color: #b91c1c !important;
            border-color: rgba(239, 68, 68, 0.4);
            background: rgba(239, 68, 68, 0.12);
            box-shadow: 0 0 14px rgba(239, 68, 68, 0.22);
        }

        .if-recent-item:hover {
            transform: translateY(-2px);
            border-color: rgba(67, 97, 238, 0.28);
        }

        .if-recent-name {
            font-size: 0.78rem;
            font-weight: 600;
            color: var(--text2) !important;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        .if-recent-meta {
            font-size: 0.68rem;
            color: var(--light) !important;
            font-family: "JetBrains Mono", monospace !important;
            margin-top: 1px;
        }

        .if-recent-state {
            display: inline-block;
            margin-top: 4px;
            font-size: 0.66rem;
            border-radius: 999px;
            padding: 2px 8px;
            font-family: "JetBrains Mono", monospace !important;
            font-weight: 600;
            border: 1px solid var(--border2);
            background: rgba(67, 97, 238, 0.08);
            color: var(--blue) !important;
        }

        .stTabs [data-baseweb="tab-list"] {
            position: relative;
            gap: 8px;
            border: 1px solid var(--border2);
            background: rgba(255, 255, 255, 0.92);
            border-radius: 13px;
            padding: 4px;
        }

        .stTabs [data-baseweb="tab"] {
            position: relative;
            overflow: hidden;
            border-radius: 10px;
            color: var(--muted) !important;
            font-weight: 600;
            transition: transform var(--motion-fast) ease, color var(--motion-fast) ease, background-color var(--motion-fast) ease, box-shadow var(--motion-fast) ease;
            border: none;
            font-family: "Outfit", sans-serif !important;
        }

        .stTabs [data-baseweb="tab"]::after {
            content: "";
            position: absolute;
            left: 18%;
            right: 18%;
            bottom: 5px;
            height: 2px;
            border-radius: 999px;
            background: linear-gradient(90deg, var(--blue), var(--indigo), var(--violet));
            transform: scaleX(0);
            transform-origin: center;
            transition: transform var(--motion-fast) ease;
        }

        .stTabs [data-baseweb="tab"]:hover {
            background: rgba(67, 97, 238, 0.1);
            color: var(--blue) !important;
            text-shadow: 0 0 10px rgba(67, 97, 238, 0.18);
            transform: translateY(-1px);
        }

        .stTabs [data-baseweb="tab"]:hover::after {
            transform: scaleX(1);
        }

        .stTabs [aria-selected="true"] {
            background: linear-gradient(135deg, var(--blue), var(--indigo));
            color: #fff !important;
            box-shadow: 0 6px 18px rgba(67, 97, 238, 0.3);
        }

        .stTabs [aria-selected="true"]::after {
            transform: scaleX(1);
            background: linear-gradient(90deg, rgba(255, 255, 255, 0.95), rgba(255, 255, 255, 0.55));
        }

        [data-testid="stTabs"] [role="tabpanel"] {
            animation: ifTabSlideX 0.3s ease both;
        }

        .stButton > button,
        .stDownloadButton > button {
            position: relative;
            overflow: hidden;
            border-radius: 12px;
            border: none;
            font-weight: 700;
            letter-spacing: 0.01em;
            background: linear-gradient(135deg, var(--blue), var(--indigo), var(--violet));
            color: #fff;
            box-shadow: 0 8px 28px rgba(67, 97, 238, 0.28);
            transition: transform var(--motion-fast) ease, box-shadow var(--motion-fast) ease, filter var(--motion-fast) ease;
        }

        .stButton > button:hover,
        .stDownloadButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 14px 34px rgba(67, 97, 238, 0.34);
            filter: brightness(1.02);
        }

        .stButton > button .if-ripple,
        .stDownloadButton > button .if-ripple {
            position: absolute;
            width: 22px;
            height: 22px;
            border-radius: 50%;
            pointer-events: none;
            background: radial-gradient(circle, rgba(255, 255, 255, 0.72), rgba(255, 255, 255, 0));
            animation: ifRipple 0.7s ease-out forwards;
            top: 0;
            left: 0;
        }

        .stTextInput input,
        .stTextArea textarea,
        div[data-baseweb="select"] > div,
        .stMultiSelect div[data-baseweb="select"] > div {
            background: #fff !important;
            border: 1px solid var(--border2) !important;
            border-radius: 11px !important;
            color: var(--text) !important;
            transition: border-color var(--motion-fast) ease, box-shadow var(--motion-fast) ease;
        }

        .stTextInput input:focus,
        .stTextArea textarea:focus,
        div[data-baseweb="select"] > div:focus-within,
        .stMultiSelect div[data-baseweb="select"] > div:focus-within {
            border-color: rgba(99, 102, 241, 0.58) !important;
            box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.16) !important;
        }

        div[data-testid="stFileUploader"] {
            position: relative;
            overflow: hidden;
            border: 2px dashed rgba(67, 97, 238, 0.26);
            border-radius: 14px;
            padding: 10px;
            background: rgba(255, 255, 255, 0.72);
            transition: transform var(--motion-fast) ease, border-color var(--motion-fast) ease, box-shadow var(--motion-fast) ease, background var(--motion-fast) ease;
            will-change: transform;
        }

        div[data-testid="stFileUploader"]::before {
            content: "";
            position: absolute;
            inset: -35%;
            background: radial-gradient(circle at center, rgba(67, 97, 238, 0.18), rgba(67, 97, 238, 0) 62%);
            opacity: 0;
            transition: opacity var(--motion-fast) ease;
            pointer-events: none;
        }

        div[data-testid="stFileUploader"]:hover {
            transform: scale(1.01);
            border-color: rgba(67, 97, 238, 0.52);
            box-shadow: 0 14px 30px rgba(67, 97, 238, 0.16);
        }

        div[data-testid="stFileUploader"]:hover::before,
        div[data-testid="stFileUploader"].if-drag-active::before {
            opacity: 1;
        }

        div[data-testid="stFileUploader"].if-drag-active {
            border-color: rgba(67, 97, 238, 0.65);
            background: linear-gradient(135deg, rgba(67, 97, 238, 0.13), rgba(123, 47, 247, 0.11), rgba(14, 165, 233, 0.1));
            animation: ifDropPulse 1.8s ease-in-out infinite;
        }

        div[data-testid="stFileUploader"].if-drop-ripple::after {
            content: "";
            position: absolute;
            left: 50%;
            top: 50%;
            width: 120px;
            height: 120px;
            border-radius: 50%;
            border: 2px solid rgba(67, 97, 238, 0.38);
            pointer-events: none;
            animation: ifDropRipple 0.75s ease-out forwards;
        }

        div[data-testid="stAlert"] {
            border: 1px solid var(--border2);
            border-radius: 12px;
            background: #fff;
        }

        div[data-testid="stDataFrame"],
        div[data-testid="stTable"] {
            border: 1px solid var(--border2);
            border-radius: 12px;
            overflow: hidden;
            background: rgba(255, 255, 255, 0.92);
        }

        div[data-testid="stProgressBar"] div[role="progressbar"] {
            background: linear-gradient(90deg, var(--blue), var(--indigo), var(--violet), var(--teal)) !important;
            background-size: 200% 100% !important;
            animation: ifShimmer 2.6s linear infinite;
        }

        code, pre {
            border-radius: 8px !important;
            border: 1px solid var(--border) !important;
            background: #f8faff !important;
            color: var(--text) !important;
        }

        [role="tooltip"] {
            border: 1px solid rgba(100, 120, 255, 0.24);
            border-radius: 10px;
            backdrop-filter: blur(8px);
            animation: ifCardRise 0.2s ease both;
        }

        .if-motion-ready .if-reveal {
            opacity: 0;
            transform: translate3d(0, 16px, 0);
            transition: opacity 0.52s ease, transform 0.52s ease;
        }

        .if-motion-ready .if-reveal.is-visible {
            opacity: 1;
            transform: translate3d(0, 0, 0);
        }

        @media (max-width: 1024px) {
            .main .block-container {
                padding-left: 1rem;
            }

            .main .block-container:has(.if-auth-screen) {
                max-width: 860px;
                min-height: auto;
            }

            .if-cap-grid {
                grid-template-columns: 1fr;
            }

            .dash-panel-grid {
                grid-template-columns: 1fr 1fr;
            }
        }

        @media (max-width: 780px) {
            .if-side-rail {
                display: none;
            }

            .main .block-container {
                padding-left: 0.8rem;
            }

            .if-topbar {
                flex-direction: column;
                align-items: flex-start;
                top: 0;
            }

            .if-brand-wrap {
                width: 100%;
                flex-wrap: wrap;
                gap: 8px;
            }

            .if-brand-div,
            .if-page-tag {
                display: none;
            }

            .if-top-actions {
                width: 100%;
                justify-content: flex-start;
                flex-wrap: wrap;
            }

            .if-user-strip {
                align-items: flex-start;
            }

            .if-user-meta {
                gap: 6px;
            }

            .main .block-container:has(.if-auth-screen) {
                min-height: auto;
                padding-top: 0.8rem;
                padding-bottom: 0.8rem;
            }

            .if-auth-screen {
                padding-top: 0;
                margin-bottom: 0.75rem;
            }

            .if-auth-brand {
                padding-top: 0;
            }

            .if-auth-brand::before {
                inset: 1.6rem 0 auto;
                height: 150px;
                border-radius: 22px;
            }

            .if-auth-logo {
                width: 74px;
                height: 74px;
                border-radius: 20px;
            }

            .if-auth-title {
                font-size: 2.35rem;
            }

            .if-auth-copy {
                font-size: 0.92rem;
            }

            .if-auth-highlights {
                gap: 0.5rem;
            }

            .if-auth-highlight {
                width: 100%;
                justify-content: center;
            }

            div[data-testid="stVerticalBlock"]:has(.if-auth-card-marker):not(:has(div[data-testid="stVerticalBlock"] .if-auth-card-marker)) {
                max-width: 100%;
                padding: 1rem;
                border-radius: 20px;
            }

            div[data-testid="stVerticalBlock"]:has(.if-auth-card-marker):not(:has(div[data-testid="stVerticalBlock"] .if-auth-card-marker)) [data-testid="stTabs"] [role="tablist"],
            div[data-testid="stVerticalBlock"]:has(.if-auth-card-marker):not(:has(div[data-testid="stVerticalBlock"] .if-auth-card-marker)) .stTabs [data-baseweb="tab-list"] {
                width: 100%;
            }

            div[data-testid="stVerticalBlock"]:has(.if-auth-card-marker):not(:has(div[data-testid="stVerticalBlock"] .if-auth-card-marker)) [data-testid="stTabs"] [role="tabpanel"] {
                max-width: 100%;
                padding: 0.95rem 0.85rem 0.85rem;
            }

            .if-auth-card-title {
                font-size: 1.2rem;
            }

            .if-auth-panel-title {
                font-size: 1.22rem;
            }

            div[data-testid="stVerticalBlock"]:has(.if-auth-card-marker):not(:has(div[data-testid="stVerticalBlock"] .if-auth-card-marker)) [data-testid="stForm"] {
                max-width: 100%;
            }

            .if-hero-gem {
                width: 78px;
                height: 78px;
            }

            .if-badge-row {
                gap: 6px;
            }

            .dash-panel-grid {
                grid-template-columns: 1fr;
            }
        }

        @media (prefers-reduced-motion: reduce) {
            html, body, [data-testid="stAppViewContainer"], [data-testid="stApp"] {
                scroll-behavior: auto;
            }

            .if-aurora,
            .if-grid-fog,
            .if-status,
            .if-gem,
            .if-hero-gem,
            .if-badge,
            .if-cap-card,
            .if-topbar,
            .if-hero,
            .section-head,
            .if-hero-title,
            .dash-panel,
            .dash-metric,
            .if-mini,
            .if-recent-item,
            [data-testid="stTabs"] [role="tabpanel"],
            div[data-testid="stProgressBar"] div[role="progressbar"] {
                animation: none !important;
            }

            .if-motion-ready .if-reveal {
                opacity: 1 !important;
                transform: none !important;
                transition: none !important;
            }

            .if-cap-card {
                opacity: 1 !important;
                transform: none !important;
            }

            .if-cap-visual *,
            .if-cap-visual::before,
            .if-cap-visual::after {
                animation: none !important;
                transition: none !important;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_live_background():
    st.markdown(
        """
        <div class="if-live-bg" aria-hidden="true">
          <div class="if-aurora a1"></div>
          <div class="if-aurora a2"></div>
          <div class="if-aurora a3"></div>
          <div class="if-aurora a4"></div>
          <div class="if-grid-fog"></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_side_rail():
    st.markdown(
        """
        <nav class="if-side-rail" aria-hidden="true">
          <div class="if-rail-logo">
            <div class="if-rail-gem">
              <svg width="24" height="24" viewBox="0 0 28 28" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M16 3L7 15.5H13.5L12 25L21 12.5H14.5L16 3Z" fill="white" fill-opacity="0.95"/>
                <rect x="4" y="6.5" width="4.5" height="1.4" rx=".7" fill="white" fill-opacity=".5"/>
                <rect x="4" y="9.2" width="3" height="1.4" rx=".7" fill="white" fill-opacity=".32"/>
                <rect x="20.5" y="17" width="3.5" height="1.4" rx=".7" fill="white" fill-opacity=".5"/>
                <rect x="21" y="19.7" width="2.5" height="1.4" rx=".7" fill="white" fill-opacity=".32"/>
              </svg>
            </div>
            <div class="if-rail-dot"></div>
          </div>
          <div class="if-rail-item on">HOME</div>
          <div class="if-rail-item">INV</div>
          <div class="if-rail-item">REV</div>
          <div class="if-rail-item">EXP</div>
          <div class="if-rail-sep"></div>
          <div class="if-rail-item">ANL</div>
          <div class="if-rail-bottom">
            <div class="if-rail-item">SET</div>
            <div class="if-rail-item">HLP</div>
          </div>
        </nav>
        """,
        unsafe_allow_html=True,
    )


def inject_motion_runtime():
    components.html(
        """
        <script>
          (() => {
            const host = window.parent;
            const doc = host && host.document;
            if (!doc) return;

            const prefersReduced = host.matchMedia && host.matchMedia("(prefers-reduced-motion: reduce)").matches;
            doc.documentElement.classList.add("if-motion-ready");

            const uploaderSelector = 'div[data-testid="stFileUploader"]';

            const formatCount = (value, decimals) => {
              if (decimals > 0) {
                return Number(value).toFixed(decimals);
              }
              return String(Math.round(value));
            };

            const animateCount = (el) => {
              const target = Number(el.dataset.countEnd);
              if (!Number.isFinite(target)) return;
              const decimals = Number(el.dataset.countDecimals || "0");
              const prefix = el.dataset.countPrefix || "";
              const suffix = el.dataset.countSuffix || "";
              const signature = `${target}|${decimals}|${prefix}|${suffix}`;

              if (el.dataset.countSignature === signature) return;
              el.dataset.countSignature = signature;

              if (prefersReduced) {
                el.textContent = `${prefix}${formatCount(target, decimals)}${suffix}`;
                return;
              }

              const start = host.performance.now();
              const duration = 900;

              const step = (timestamp) => {
                const t = Math.min((timestamp - start) / duration, 1);
                const eased = 1 - Math.pow(1 - t, 3);
                const current = target * eased;
                el.textContent = `${prefix}${formatCount(current, decimals)}${suffix}`;
                if (t < 1) {
                  host.requestAnimationFrame(step);
                }
              };

              host.requestAnimationFrame(step);
            };

            const runCountups = () => {
              doc.querySelectorAll(".if-countup").forEach(animateCount);
            };

            if (!host.__ifRevealObserver && !prefersReduced && host.IntersectionObserver) {
              host.__ifRevealObserver = new host.IntersectionObserver(
                (entries) => {
                  entries.forEach((entry) => {
                    if (entry.isIntersecting) {
                      entry.target.classList.add("is-visible");
                      host.__ifRevealObserver.unobserve(entry.target);
                    }
                  });
                },
                { threshold: 0.12, rootMargin: "0px 0px -8% 0px" },
              );
            }

            const observeReveals = () => {
              const revealNodes = doc.querySelectorAll(".if-reveal");
              if (prefersReduced) {
                revealNodes.forEach((node) => node.classList.add("is-visible"));
                return;
              }

              const observer = host.__ifRevealObserver;
              if (!observer) {
                revealNodes.forEach((node) => node.classList.add("is-visible"));
                return;
              }
              revealNodes.forEach((node) => {
                if (node.dataset.revealBound === "1") return;
                node.dataset.revealBound = "1";
                observer.observe(node);
              });
            };

            const scheduleHydrate = () => {
              if (host.__ifHydrateQueued) return;
              host.__ifHydrateQueued = true;
              host.requestAnimationFrame(() => {
                host.__ifHydrateQueued = false;
                observeReveals();
                runCountups();
              });
            };

            if (!host.__ifMotionMutationObserver) {
              host.__ifMotionMutationObserver = new host.MutationObserver(() => {
                scheduleHydrate();
              });
              host.__ifMotionMutationObserver.observe(doc.body, {
                childList: true,
                subtree: true,
              });
            }

            if (!host.__ifRippleBound) {
              doc.addEventListener(
                "click",
                (event) => {
                  const button = event.target && event.target.closest(".stButton > button, .stDownloadButton > button");
                  if (!button) return;

                  const rect = button.getBoundingClientRect();
                  const ripple = doc.createElement("span");
                  ripple.className = "if-ripple";
                  ripple.style.left = `${event.clientX - rect.left}px`;
                  ripple.style.top = `${event.clientY - rect.top}px`;
                  button.appendChild(ripple);
                  host.setTimeout(() => ripple.remove(), 720);
                },
                true,
              );
              host.__ifRippleBound = true;
            }

            if (!host.__ifUploaderMotionBound) {
              const clearDragState = () => {
                doc.querySelectorAll(`${uploaderSelector}.if-drag-active`).forEach((node) => {
                  node.classList.remove("if-drag-active");
                });
              };

              doc.addEventListener(
                "dragover",
                (event) => {
                  const uploader = event.target && event.target.closest(uploaderSelector);
                  if (!uploader) return;
                  uploader.classList.add("if-drag-active");
                },
                true,
              );

              doc.addEventListener(
                "dragleave",
                (event) => {
                  const uploader = event.target && event.target.closest(uploaderSelector);
                  if (!uploader) return;
                  const related = event.relatedTarget;
                  if (related && uploader.contains(related)) return;
                  uploader.classList.remove("if-drag-active");
                },
                true,
              );

              doc.addEventListener(
                "drop",
                (event) => {
                  const uploader = event.target && event.target.closest(uploaderSelector);
                  if (uploader) {
                    uploader.classList.remove("if-drag-active");
                    uploader.classList.remove("if-drop-ripple");
                    void uploader.offsetWidth;
                    uploader.classList.add("if-drop-ripple");
                    host.setTimeout(() => uploader.classList.remove("if-drop-ripple"), 760);
                  }
                  clearDragState();
                },
                true,
              );

              host.__ifUploaderMotionBound = true;
            }

            scheduleHydrate();
          })();
        </script>
        """,
        height=0,
        width=0,
    )


def render_sidebar_brand():
    st.markdown(
        """
        <div class="space-brand">
          <div class="space-logo">
            <svg width="26" height="26" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
              <defs>
                <linearGradient id="if_side_doc" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" stop-color="#f8fbff"/>
                  <stop offset="100%" stop-color="#dbeafe"/>
                </linearGradient>
                <linearGradient id="if_side_stamp" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" stop-color="#0ea5e9"/>
                  <stop offset="100%" stop-color="#7b2ff7"/>
                </linearGradient>
              </defs>
              <path d="M30 10h28l16 16v46c0 6.6-5.4 12-12 12H30c-6.6 0-12-5.4-12-12V22c0-6.6 5.4-12 12-12Z" fill="url(#if_side_doc)"/>
              <path d="M58 10v16h16" fill="none" stroke="#b8c7ff" stroke-width="6" stroke-linecap="round" stroke-linejoin="round"/>
              <rect x="34" y="40" width="30" height="7" rx="3.5" fill="#5b21b6"/>
              <rect x="34" y="53" width="24" height="7" rx="3.5" fill="#7c3aed"/>
              <circle cx="63" cy="64" r="10" fill="url(#if_side_stamp)"/>
              <path d="M63 58.8v10.4M57.8 64h10.4" stroke="#f8fafc" stroke-width="3.2" stroke-linecap="round"/>
            </svg>
          </div>
          <div>
            <div class="space-brand-title">invoiceflow</div>
            <div class="space-brand-sub">Invoice Workspace</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_main_header():
    st.markdown(
        """
        <div class="if-hero">
          <div class="if-hero-rings" aria-hidden="true">
            <div class="if-hero-ring"></div>
            <div class="if-hero-ring"></div>
            <div class="if-hero-ring"></div>
          </div>
          <div class="if-hero-logo-wrap">
            <div class="if-hero-gem" aria-hidden="true">
              <svg viewBox="0 0 80 80" xmlns="http://www.w3.org/2000/svg">
                <defs>
                  <linearGradient id="if_logo_hero_doc" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stop-color="#f8fbff"/>
                    <stop offset="100%" stop-color="#dbeafe"/>
                  </linearGradient>
                  <linearGradient id="if_logo_hero_line" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stop-color="#4361ee"/>
                    <stop offset="100%" stop-color="#7b2ff7"/>
                  </linearGradient>
                  <linearGradient id="if_logo_hero_stamp" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stop-color="#06d6a0"/>
                    <stop offset="100%" stop-color="#0ea5e9"/>
                  </linearGradient>
                </defs>
                <path d="M22 10h28l16 16v40c0 5.5-4.5 10-10 10H22c-5.5 0-10-4.5-10-10V20c0-5.5 4.5-10 10-10Z" fill="url(#if_logo_hero_doc)"/>
                <path d="M50 10v16h16" fill="none" stroke="#bfd0ff" stroke-width="3.8" stroke-linecap="round" stroke-linejoin="round"/>
                <rect x="27" y="34" width="25" height="5" rx="2.5" fill="url(#if_logo_hero_line)"/>
                <rect x="27" y="43" width="19" height="5" rx="2.5" fill="#8b5cf6"/>
                <rect x="27" y="52" width="15" height="5" rx="2.5" fill="#a78bfa"/>
                <circle cx="55" cy="53" r="9" fill="url(#if_logo_hero_stamp)"/>
                <path d="M55 47.5v11M49.5 53h11" stroke="#f8fafc" stroke-width="2.8" stroke-linecap="round"/>
              </svg>
            </div>
          </div>
          <div class="if-hero-title">invoiceflow</div>
          <div class="if-hero-sub">
            The intelligent invoice processing workspace. Upload, extract, review, and export structured data with production-grade reliability.
          </div>
          <div class="if-badge-row">
            <span class="if-badge"><span class="if-badge-dot d1"></span>OCR Extraction</span>
            <span class="if-badge"><span class="if-badge-dot d2"></span>Batch Processing</span>
            <span class="if-badge"><span class="if-badge-dot d3"></span>Smart Review</span>
            <span class="if-badge"><span class="if-badge-dot d4"></span>Instant Export</span>
            <span class="if-badge"><span class="if-badge-dot d5"></span>Live Analytics</span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_capability_cards():
    st.markdown(
        """
        <div class="if-cap-head">
          <div>
            <div class="if-cap-title"><b>Platform</b> Capabilities</div>
            <div class="if-cap-sub">Everything the platform does for you, visualized and production-ready.</div>
          </div>
        </div>
        <div class="if-cap-grid">
          <div class="if-cap-card">
            <div class="if-cap-visual v1">
              <div class="if-cap-label">OCR FLOW</div>
              <div class="cap-ocr-wrap">
                <div class="cap-ocr-doc">
                  <div class="cap-ocr-scan"></div>
                  <div class="cap-ocr-line w1"></div>
                  <div class="cap-ocr-line w2"></div>
                  <div class="cap-ocr-line w3"></div>
                  <div class="cap-ocr-line w4"></div>
                </div>
                <div class="cap-ocr-tags">
                  <span class="cap-pill">VENDOR</span>
                  <span class="cap-pill">AMOUNT</span>
                  <span class="cap-pill">DATE</span>
                </div>
              </div>
            </div>
            <div class="if-cap-body">
              <div class="if-cap-icon">OCR</div>
              <div class="if-cap-name">AI OCR Extraction</div>
              <div class="if-cap-desc">Extracts vendor, dates, amounts, taxes, and line-items from scanned invoices.</div>
            </div>
          </div>
          <div class="if-cap-card">
            <div class="if-cap-visual v2">
              <div class="if-cap-label">BATCH PIPELINE</div>
              <div class="cap-batch-list">
                <div class="cap-batch-item">
                  <span class="cap-batch-dot"></span>
                  <div class="cap-batch-bar"><span class="cap-batch-fill"></span></div>
                </div>
                <div class="cap-batch-item">
                  <span class="cap-batch-dot"></span>
                  <div class="cap-batch-bar"><span class="cap-batch-fill"></span></div>
                </div>
                <div class="cap-batch-item">
                  <span class="cap-batch-dot"></span>
                  <div class="cap-batch-bar"><span class="cap-batch-fill"></span></div>
                </div>
              </div>
            </div>
            <div class="if-cap-body">
              <div class="if-cap-icon">UP</div>
              <div class="if-cap-name">Batch Upload</div>
              <div class="if-cap-desc">Upload many files or full zip folders and process them in one workflow.</div>
            </div>
          </div>
          <div class="if-cap-card">
            <div class="if-cap-visual v3">
              <div class="if-cap-label">REVIEW LOOP</div>
              <div class="cap-review-card">
                <div class="cap-review-row">
                  <div class="cap-review-line r1"></div>
                  <span class="cap-review-check"></span>
                </div>
                <div class="cap-review-row">
                  <div class="cap-review-line r2"></div>
                  <span class="cap-review-check"></span>
                </div>
                <div class="cap-review-row">
                  <div class="cap-review-line r3"></div>
                  <span class="cap-review-check"></span>
                </div>
              </div>
            </div>
            <div class="if-cap-body">
              <div class="if-cap-icon">REV</div>
              <div class="if-cap-name">Smart Review</div>
              <div class="if-cap-desc">Automatic review context with editable JSON and confidence visibility.</div>
            </div>
          </div>
          <div class="if-cap-card">
            <div class="if-cap-visual v4">
              <div class="if-cap-label">EXPORT HUB</div>
              <div class="cap-export-scene">
                <div class="cap-export-core">EXP</div>
                <span class="cap-export-chip c1">JSON</span>
                <span class="cap-export-chip c2">CSV</span>
                <span class="cap-export-chip c3">XLSX</span>
              </div>
            </div>
            <div class="if-cap-body">
              <div class="if-cap-icon">EXP</div>
              <div class="if-cap-name">Export Ready</div>
              <div class="if-cap-desc">Generate JSON, CSV, and Excel outputs directly from reviewed invoices.</div>
            </div>
          </div>
          <div class="if-cap-card">
            <div class="if-cap-visual v5">
              <div class="if-cap-label">LIVE METRICS</div>
              <div class="cap-live-chart">
                <div class="cap-live-bars">
                  <span class="cap-live-bar b1"></span>
                  <span class="cap-live-bar b2"></span>
                  <span class="cap-live-bar b3"></span>
                  <span class="cap-live-bar b4"></span>
                  <span class="cap-live-bar b5"></span>
                  <span class="cap-live-bar b6"></span>
                </div>
                <div class="cap-live-spark"></div>
              </div>
            </div>
            <div class="if-cap-body">
              <div class="if-cap-icon">OPS</div>
              <div class="if-cap-name">Live Status</div>
              <div class="if-cap-desc">Backend health, active invoice, and operational state are visible in real time.</div>
            </div>
          </div>
          <div class="if-cap-card">
            <div class="if-cap-visual v6">
              <div class="if-cap-label">SECURE TRACE</div>
              <div class="cap-sec-scene">
                <div class="cap-sec-shield"><span class="cap-sec-lock"></span></div>
                <div class="cap-sec-bars">
                  <div class="cap-sec-bar"><span class="cap-sec-fill"></span></div>
                  <div class="cap-sec-bar"><span class="cap-sec-fill"></span></div>
                  <div class="cap-sec-bar"><span class="cap-sec-fill"></span></div>
                </div>
              </div>
            </div>
            <div class="if-cap-body">
              <div class="if-cap-icon">SEC</div>
              <div class="if-cap-name">Secure Pipeline</div>
              <div class="if-cap-desc">Controlled upload/review/export flow with backend validation and traceability.</div>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def format_duration(seconds: Optional[float]) -> str:
    if seconds is None:
        return "n/a"
    total = max(0, int(seconds))
    hours, remainder = divmod(total, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours:
        return f"{hours}h {minutes}m"
    if minutes:
        return f"{minutes}m {secs}s"
    return f"{secs}s"


def render_dashboard_panel(backend_ok: bool, backend_status: str):
    backend_class = "status-ok" if backend_ok else "status-bad"
    backend_label = "ONLINE" if backend_ok else "OFFLINE"
    backend_health_text = "HEALTHY" if backend_ok else "UNHEALTHY"
    health_percent = 100 if backend_ok else 32
    uploaded_count = len(st.session_state.last_uploads)
    active_invoice = st.session_state.active_invoice_id or "-"
    started_at = st.session_state.get("backend_started_at")
    uptime = format_duration(time.time() - started_at) if started_at else "n/a"
    panel = f"""
    <div class="dash-panel">
      <div class="dash-head">
        <div class="dash-title">Invoice Overview</div>
        <div class="status-pill {backend_class}">{backend_label}</div>
      </div>
      <div class="dash-panel-grid">
        <div class="dash-metric dash-metric-health">
          <div class="dash-label">Backend Healthy</div>
          <div class="dash-value if-countup" data-count-end="{health_percent}" data-count-decimals="0" data-count-suffix="%">{health_percent}%</div>
          <div class="dash-live"><span class="dash-live-dot"></span>{backend_health_text} | {html.escape(str(backend_status))}</div>
        </div>
        <div class="dash-metric">
          <div class="dash-label">Uploaded IDs</div>
          <div class="dash-value if-countup" data-count-end="{uploaded_count}" data-count-decimals="0">{uploaded_count}</div>
        </div>
        <div class="dash-metric">
          <div class="dash-label">Active Invoice</div>
          <div class="dash-value">{active_invoice}</div>
        </div>
        <div class="dash-metric">
          <div class="dash-label">Backend Uptime</div>
          <div class="dash-value">{uptime}</div>
        </div>
      </div>
      <div class="dash-health-meter">
        <div class="dash-label">System Health</div>
        <div class="dash-health-track">
          <div class="dash-health-fill" style="--health-target:{health_percent}%;"></div>
        </div>
      </div>
      <div class="dash-label" style="margin-top:10px;">Live sync with backend endpoint and session state telemetry.</div>
    </div>
    """
    st.markdown(panel, unsafe_allow_html=True)


def render_section_intro(title: str, subtitle: str):
    st.markdown(
        f"""
        <div class="section-head if-reveal">
          <div class="section-title">{title}</div>
          <div class="section-sub">{subtitle}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def response_payload(res: Any) -> Any:
    if isinstance(res, dict):
        return res
    try:
        return res.json()
    except Exception:
        return {"error": getattr(res, "text", "Unexpected response payload.")}


def ensure_dict_payload(payload: Any) -> Dict[str, Any]:
    return payload if isinstance(payload, dict) else {"raw_response": payload}


REVIEW_READY_STATUSES = {"completed", "reviewed"}
REVIEW_TERMINAL_STATUSES = REVIEW_READY_STATUSES | {"failed"}
REVIEW_POLL_STATUSES = {"pending", "processing", "uploaded", "queued", "initialization"}


def start_processing_for_upload(
    invoice_id: str,
    use_cache: bool,
    prefer_handwriting_ocr: bool,
) -> Dict[str, Any]:
    proc_res = post_json(
        f"{st.session_state.base_url}/process/start",
        {
            "invoice_id": invoice_id,
            "use_cache": use_cache,
            "prefer_handwriting_ocr": prefer_handwriting_ocr,
        },
    )
    if isinstance(proc_res, dict) and proc_res.get("_error"):
        return {"error": proc_res["_error"]}
    payload = ensure_dict_payload(response_payload(proc_res))
    if getattr(proc_res, "status_code", 200) != 200:
        detail = payload.get("detail") or payload.get("error") or str(payload)
        return {"error": detail}
    return payload


def set_active_invoice(invoice_id: str):
    st.session_state.active_invoice_id = invoice_id
    st.session_state.export_id = invoice_id
    if st.session_state.get("review_loaded_invoice_id") != invoice_id:
        st.session_state.review_details = None
        st.session_state.review_json = ""
        st.session_state.review_loaded_invoice_id = None
        st.session_state.review_load_error = None


def load_review_details_for_invoice(invoice_id: str) -> Tuple[bool, Optional[str]]:
    previous_details = st.session_state.get("review_details")
    previous_status = (
        str(previous_details.get("processing_status") or "").lower()
        if isinstance(previous_details, dict)
        else ""
    )
    previous_ready_for_review = (
        isinstance(previous_details, dict)
        and (bool(previous_details.get("ready_for_review")) or previous_status in REVIEW_READY_STATUSES)
    )
    previous_loaded_invoice_id = st.session_state.get("review_loaded_invoice_id")
    previous_review_json = st.session_state.get("review_json")

    res = get_json(f"{st.session_state.base_url}/review/{invoice_id}/details")
    if isinstance(res, dict) and res.get("_error"):
        message = f"Backend not reachable: {res['_error']}"
        st.session_state.review_details = None
        st.session_state.review_json = ""
        st.session_state.review_loaded_invoice_id = invoice_id
        st.session_state.review_load_error = message
        return False, message

    data = response_payload(res)
    if getattr(res, "status_code", None) == 200:
        if not isinstance(data, dict):
            message = "Unexpected review response format."
            st.session_state.review_details = None
            st.session_state.review_json = ""
            st.session_state.review_loaded_invoice_id = invoice_id
            st.session_state.review_load_error = message
            return False, message
        processing_status = str(data.get("processing_status") or "pending").lower()
        extracted_data = data.get("extracted_data")
        confidence_scores = data.get("confidence_scores")
        details_payload = {
            **data,
            "invoice_id": data.get("invoice_id") or invoice_id,
            "filename": data.get("filename") or data.get("file_name") or "-",
            "extracted_data": extracted_data if isinstance(extracted_data, dict) else {},
            "confidence_scores": confidence_scores if isinstance(confidence_scores, dict) else {},
            "processing_status": processing_status,
            "ready_for_review": bool(data.get("ready_for_review")) or processing_status in REVIEW_READY_STATUSES,
            "progress": int(data.get("progress") or 0),
            "current_step": data.get("current_step"),
            "error_message": data.get("error_message"),
        }
        st.session_state.review_details = details_payload
        should_refresh_json = (
            previous_loaded_invoice_id != invoice_id
            or not previous_review_json
            or (details_payload.get("ready_for_review") and not previous_ready_for_review)
        )
        if should_refresh_json and details_payload.get("ready_for_review"):
            st.session_state.review_json = json.dumps(details_payload.get("extracted_data", {}), indent=2)
        st.session_state.review_loaded_invoice_id = invoice_id
        st.session_state.review_load_error = None
        if details_payload.get("ready_for_review"):
            return True, None
        message = f"Invoice is {processing_status}; waiting for extraction."
        st.session_state.review_load_error = message
        return False, message

    detail = data.get("detail") if isinstance(data, dict) else data
    message = str(detail)

    # Fallback: use process status data when the review endpoint is not ready.
    status_res = get_json(f"{st.session_state.base_url}/process/status/{invoice_id}")
    if not (isinstance(status_res, dict) and status_res.get("_error")):
        status_data = response_payload(status_res)
        if getattr(status_res, "status_code", None) == 200 and isinstance(status_data, dict):
            process_state = str(status_data.get("status") or "pending").lower()
            fallback_details = {
                "invoice_id": invoice_id,
                "filename": "-",
                "extracted_data": status_data.get("extracted_data") if isinstance(status_data.get("extracted_data"), dict) else {},
                "confidence_scores": status_data.get("confidence_scores") if isinstance(status_data.get("confidence_scores"), dict) else {},
                "processing_status": process_state,
                "review_status": None,
                "ready_for_review": process_state in REVIEW_READY_STATUSES,
                "progress": int(status_data.get("progress") or 0),
                "current_step": status_data.get("current_step"),
                "error_message": status_data.get("error_message"),
            }
            st.session_state.review_details = fallback_details
            should_refresh_json = (
                previous_loaded_invoice_id != invoice_id
                or not previous_review_json
                or (fallback_details["ready_for_review"] and not previous_ready_for_review)
            )
            if should_refresh_json and fallback_details["ready_for_review"]:
                st.session_state.review_json = json.dumps(fallback_details.get("extracted_data", {}), indent=2)
            st.session_state.review_loaded_invoice_id = invoice_id
            st.session_state.review_load_error = message
            if fallback_details["ready_for_review"]:
                return True, None
            return False, f"{message} (status: {process_state})"

    st.session_state.review_details = None
    st.session_state.review_json = ""
    st.session_state.review_loaded_invoice_id = invoice_id
    st.session_state.review_load_error = message
    return False, message


def upload_invoice_entries(
    entries: List[Tuple[str, bytes, str]],
    auto_process: bool,
    use_cache: bool,
    prefer_handwriting_ocr: bool,
) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []
    total = len(entries)
    progress = st.progress(0.0) if total else None

    for index, (name, content, mime) in enumerate(entries, start=1):
        uploaded_at = time.time()
        res = upload_single_file(st.session_state.base_url, name, content, mime)
        if isinstance(res, dict) and res.get("_error"):
            results.append({"file": name, "status": "error", "data": res["_error"], "processing": None})
            st.session_state.upload_activity.insert(
                0,
                {
                    "file": name,
                    "invoice_id": "-",
                    "status": "failed",
                    "uploaded_at": uploaded_at,
                    "detail": str(res["_error"]),
                },
            )
        else:
            data = response_payload(res)
            status_code = getattr(res, "status_code", "error")
            invoice_id = data.get("invoice_id") if isinstance(data, dict) else None
            if invoice_id:
                st.session_state.last_uploads.append(invoice_id)
                set_active_invoice(invoice_id)
            processing: Optional[Dict[str, Any]] = None
            if auto_process and status_code == 200 and invoice_id:
                processing = start_processing_for_upload(
                    invoice_id,
                    use_cache,
                    prefer_handwriting_ocr,
                )

            results.append(
                {
                    "file": name,
                    "status": status_code,
                    "data": data,
                    "processing": processing,
                }
            )
            processing_state = "queued"
            if isinstance(processing, dict):
                if processing.get("error"):
                    processing_state = "processing_failed"
                elif processing.get("status"):
                    processing_state = str(processing.get("status"))
            st.session_state.upload_activity.insert(
                0,
                {
                    "file": name,
                    "invoice_id": invoice_id or "-",
                    "status": "done" if isinstance(status_code, int) and 200 <= status_code < 300 else f"failed ({status_code})",
                    "uploaded_at": uploaded_at,
                    "detail": processing_state if auto_process else "uploaded",
                },
            )

        if progress:
            progress.progress(index / total)

    st.session_state.upload_activity = st.session_state.upload_activity[:20]

    if progress:
        progress.empty()
    return results


def render_upload_results(results: List[Dict[str, Any]], auto_process: bool):
    if not results:
        st.info("No files were uploaded.")
        return

    uploaded = 0
    failed = 0
    processing_started = 0
    rows = []

    for item in results:
        status = item.get("status")
        uploaded_ok = isinstance(status, int) and 200 <= status < 300
        if uploaded_ok:
            uploaded += 1
        else:
            failed += 1

        data = item.get("data") if isinstance(item.get("data"), dict) else {}
        invoice_id = data.get("invoice_id") if isinstance(data, dict) else "-"

        process_text = "Not requested"
        process_info = item.get("processing")
        if auto_process:
            if isinstance(process_info, dict):
                if process_info.get("error"):
                    process_text = "Failed"
                else:
                    process_text = process_info.get("status") or process_info.get("message") or "Started"
                    processing_started += 1
            else:
                process_text = "Skipped"

        rows.append(
            {
                "File": item.get("file"),
                "Upload": "Success" if uploaded_ok else f"Failed ({status})",
                "Invoice ID": invoice_id,
                "Auto Processing": process_text,
            }
        )

    metric_columns = st.columns(4 if auto_process else 3)
    metric_columns[0].metric("Files", len(results))
    metric_columns[1].metric("Uploaded", uploaded)
    metric_columns[2].metric("Failed", failed)
    if auto_process:
        metric_columns[3].metric("Processing Queued", processing_started)

    st.dataframe(rows, width='stretch')
    with st.expander("View full upload responses"):
        st.json(results)


def relative_time_text(timestamp: Optional[float]) -> str:
    if not timestamp:
        return "just now"
    diff = max(0, int(time.time() - timestamp))
    if diff < 60:
        return f"{diff}s ago"
    if diff < 3600:
        return f"{diff // 60}m ago"
    if diff < 86400:
        return f"{diff // 3600}h ago"
    return f"{diff // 86400}d ago"


def render_recent_upload_panel():
    activity = st.session_state.upload_activity or []
    completed = sum(1 for item in activity if str(item.get("status", "")).startswith("done"))
    running = sum(
        1
        for item in activity
        if str(item.get("detail", "")).lower() in {"processing", "queued"}
    )
    failed = sum(1 for item in activity if "failed" in str(item.get("status", "")).lower())

    rows: List[str] = []
    for item in activity[:8]:
        file_name = html.escape(str(item.get("file") or "uploaded_file"))
        invoice_id = html.escape(str(item.get("invoice_id") or "-"))
        status = html.escape(str(item.get("status") or "unknown"))
        status_text = str(item.get("status") or "").lower()
        detail_text = str(item.get("detail") or "").lower()
        if "fail" in status_text:
            state_class = "state-failed"
        elif "done" in status_text or "success" in status_text or "complete" in status_text:
            state_class = "state-done"
        elif detail_text in {"processing", "queued", "running"} or "run" in status_text or "queue" in status_text:
            state_class = "state-running"
        else:
            state_class = ""
        when = relative_time_text(item.get("uploaded_at"))
        rows.append(
            f"""
            <div class="if-recent-item">
              <div class="if-recent-name">{file_name}</div>
              <div class="if-recent-meta">{when} | {invoice_id}</div>
              <span class="if-recent-state {state_class}">{status}</span>
            </div>
            """
        )

    if not rows:
        rows.append(
            """
            <div class="if-recent-item">
              <div class="if-recent-name">No files uploaded yet</div>
              <div class="if-recent-meta">Upload from the left panel to see live activity</div>
            </div>
            """
        )

    st.markdown(
        f"""
        <div class="if-recent-shell if-reveal">
          <div class="if-recent-head">
            <div class="if-recent-title">Recent Files</div>
            <div class="if-recent-sub">Latest processed invoices in this session</div>
          </div>
          <div class="if-recent-body">
            <div class="if-recent-grid">
              <div class="if-mini if-mini-done">
                <div class="if-mini-val if-countup" data-count-end="{completed}" data-count-decimals="0">{completed}</div>
                <div class="if-mini-lbl">DONE</div>
              </div>
              <div class="if-mini if-mini-running">
                <div class="if-mini-val if-countup" data-count-end="{running}" data-count-decimals="0">{running}</div>
                <div class="if-mini-lbl">RUNNING</div>
              </div>
              <div class="if-mini if-mini-failed">
                <div class="if-mini-val if-countup" data-count-end="{failed}" data-count-decimals="0">{failed}</div>
                <div class="if-mini-lbl">FAILED</div>
              </div>
            </div>
            {''.join(rows)}
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def init_state():
    if st.session_state.get("app_boot_marker") != APP_BOOT_MARKER:
        st.session_state.app_boot_marker = APP_BOOT_MARKER
        st.session_state.auth_token = None
        st.session_state.auth_user = None
        st.session_state.auth_notice = "Please sign in to continue."
    if "backend_port" not in st.session_state:
        st.session_state.backend_port = 8000
    if "base_url" not in st.session_state:
        st.session_state.base_url = f"http://127.0.0.1:{st.session_state.backend_port}/api"
    if "auth_token" not in st.session_state:
        st.session_state.auth_token = None
    if "auth_user" not in st.session_state:
        st.session_state.auth_user = None
    if "auth_notice" not in st.session_state:
        st.session_state.auth_notice = None
    if "history" not in st.session_state:
        st.session_state.history = []
    if "review_details" not in st.session_state:
        st.session_state.review_details = None
    if "review_json" not in st.session_state:
        st.session_state.review_json = ""
    if "review_loaded_invoice_id" not in st.session_state:
        st.session_state.review_loaded_invoice_id = None
    if "review_load_error" not in st.session_state:
        st.session_state.review_load_error = None
    if "review_auto_refresh" not in st.session_state:
        st.session_state.review_auto_refresh = True
    if "last_uploads" not in st.session_state:
        st.session_state.last_uploads = []
    if "upload_activity" not in st.session_state:
        st.session_state.upload_activity = []
    if "active_invoice_id" not in st.session_state:
        st.session_state.active_invoice_id = None
    if "export_id" not in st.session_state:
        st.session_state.export_id = ""
    if "process_status" not in st.session_state:
        st.session_state.process_status = None
    if "backend_proc" not in st.session_state:
        st.session_state.backend_proc = None
    if "backend_started_at" not in st.session_state:
        st.session_state.backend_started_at = None
    if "backend_autostart_attempted" not in st.session_state:
        st.session_state.backend_autostart_attempted = False
    if "backend_ok" not in st.session_state:
        st.session_state.backend_ok = False
    if "backend_status" not in st.session_state:
        st.session_state.backend_status = "unchecked"
    if "backend_health_checked_at" not in st.session_state:
        st.session_state.backend_health_checked_at = 0.0
    if "backend_health_base_url" not in st.session_state:
        st.session_state.backend_health_base_url = ""
    if "erp_url" not in st.session_state:
        st.session_state.erp_url = "http://localhost:8503"
    if "erp_launch_nonce" not in st.session_state:
        st.session_state.erp_launch_nonce = 0
    if "erp_proc" not in st.session_state:
        st.session_state.erp_proc = None
    if "erp_started_at" not in st.session_state:
        st.session_state.erp_started_at = None
    if "erp_ready_url" not in st.session_state:
        st.session_state.erp_ready_url = None
    if "upload_prefer_handwriting_ocr" not in st.session_state:
        st.session_state.upload_prefer_handwriting_ocr = False
    if "process_prefer_handwriting_ocr" not in st.session_state:
        st.session_state.process_prefer_handwriting_ocr = False

    # Always re-evaluate backend target so stale sessions don't stay pinned to a bad port.
    sync_backend_endpoint()


def clear_user_workspace_state():
    st.session_state.history = []
    st.session_state.review_details = None
    st.session_state.review_json = ""
    st.session_state.review_loaded_invoice_id = None
    st.session_state.review_load_error = None
    st.session_state.review_auto_refresh = True
    st.session_state.last_uploads = []
    st.session_state.upload_activity = []
    st.session_state.active_invoice_id = None
    st.session_state.export_id = ""
    st.session_state.process_status = None
    st.session_state.review_notes = ""
    st.session_state.review_approved = True


def clear_auth_state(notice: Optional[str] = None):
    st.session_state.auth_token = None
    st.session_state.auth_user = None
    st.session_state.auth_notice = notice
    clear_user_workspace_state()


def set_authenticated_user(token: str, user: Dict[str, Any]):
    st.session_state.auth_token = token
    st.session_state.auth_user = user
    st.session_state.auth_notice = None


def api_headers(token: Optional[str] = None) -> dict:
    selected_token = token if token is not None else st.session_state.get("auth_token")
    if not selected_token:
        return {}
    return {"Authorization": f"Bearer {selected_token}"}


def error_detail(payload: Any) -> str:
    if isinstance(payload, dict):
        detail = payload.get("detail") or payload.get("error") or payload.get("message")
        if isinstance(detail, (dict, list)):
            return json.dumps(detail)
        if detail is not None:
            return str(detail)
    return str(payload)


def handle_api_auth_failure(res: Any, use_auth: bool = True):
    if not use_auth or isinstance(res, dict):
        return
    if getattr(res, "status_code", None) != 401:
        return
    if not st.session_state.get("auth_token"):
        return
    payload = response_payload(res)
    detail = error_detail(payload)
    message = "Your session expired. Please sign in again."
    if detail and detail != "None":
        message = f"{message} {detail}"
    clear_auth_state(message)


def fetch_current_user_profile(token: Optional[str] = None) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    try:
        response = requests.get(
            f"{st.session_state.base_url}/auth/me",
            headers=api_headers(token),
            timeout=10.0,
        )
    except RequestException as exc:
        return None, f"Backend not reachable: {exc}"
    payload = response_payload(response)
    if response.status_code == 200 and isinstance(payload, dict):
        return payload, None
    return None, error_detail(payload)


def ensure_authenticated_user() -> bool:
    token = st.session_state.get("auth_token")
    auth_user = st.session_state.get("auth_user")
    if isinstance(auth_user, dict) and auth_user.get("email"):
        return True

    # Support presentation/demo deployments where backend auth is disabled.
    profile, error = fetch_current_user_profile(token)
    if not token and not error and isinstance(profile, dict) and profile.get("email"):
        st.session_state.auth_user = profile
        st.session_state.auth_notice = None
        return True
    if not token:
        return False
    if error:
        clear_auth_state(f"Please sign in again. {error}")
        return False
    st.session_state.auth_user = profile
    return True


def authenticate_user(email: str, password: str) -> Optional[str]:
    email = email.strip().lower()
    if not email or not password:
        return "Email and password are required."

    response = post_json(
        f"{st.session_state.base_url}/auth/login",
        {"email": email, "password": password},
        use_auth=False,
        timeout=20.0,
    )
    if isinstance(response, dict) and response.get("_error"):
        return response["_error"]

    payload = ensure_dict_payload(response_payload(response))
    if getattr(response, "status_code", None) != 200:
        return error_detail(payload)

    token = payload.get("access_token")
    if not token:
        return "Login completed, but no access token was returned."

    inline_profile = {
        "id": payload.get("user_id"),
        "email": payload.get("email"),
        "full_name": payload.get("full_name"),
        "company": payload.get("company"),
        "role": payload.get("role"),
        "created_at": payload.get("created_at"),
    }
    if inline_profile.get("email") and inline_profile.get("full_name"):
        set_authenticated_user(token, inline_profile)
        return None

    profile, error = fetch_current_user_profile(token)
    if error:
        return f"Login succeeded, but loading your profile failed: {error}"

    set_authenticated_user(token, profile)
    return None


def register_user(full_name: str, company: str, email: str, password: str, confirm_password: str) -> Optional[str]:
    full_name = full_name.strip()
    company = company.strip()
    email = email.strip().lower()

    if not full_name or not company or not email or not password:
        return "Full name, company, email, and password are required."
    if password != confirm_password:
        return "Passwords do not match."

    response = post_json(
        f"{st.session_state.base_url}/auth/register",
        {
            "full_name": full_name,
            "company": company,
            "email": email,
            "password": password,
        },
        use_auth=False,
        timeout=20.0,
    )
    if isinstance(response, dict) and response.get("_error"):
        return response["_error"]

    payload = ensure_dict_payload(response_payload(response))
    if getattr(response, "status_code", None) != 200:
        return error_detail(payload)

    return authenticate_user(email, password)


def render_auth_gate():
    auth_card = st.container()
    with auth_card:
        st.markdown(
            """
            <style>
            .main .block-container:has(.if-simple-auth-screen) {
                max-width: 500px;
                min-height: calc(100vh - 2.5rem);
                display: flex;
                flex-direction: column;
                justify-content: center;
                padding-top: 1rem;
                padding-bottom: 1rem;
            }

            .if-simple-auth-screen {
                display: none;
            }

            div[data-testid="stVerticalBlock"]:has(.if-simple-auth-card-marker):not(:has(div[data-testid="stVerticalBlock"] .if-simple-auth-card-marker)) {
                width: 100%;
                max-width: 100%;
                margin: 0 auto;
                padding: 1.5rem;
                border-radius: 22px;
                border: 1px solid rgba(226, 232, 240, 0.92);
                background: rgba(255, 255, 255, 0.94);
                box-shadow: 0 18px 40px rgba(15, 23, 42, 0.08);
            }

            .if-simple-auth-head {
                text-align: center;
                margin-bottom: 1rem;
            }

            .if-simple-auth-title {
                color: var(--text) !important;
                font-family: "Outfit", sans-serif !important;
                font-size: 2rem;
                font-weight: 800;
                line-height: 1.05;
                letter-spacing: -0.04em;
            }

            .if-simple-auth-copy {
                margin-top: 0.45rem;
                color: var(--muted) !important;
                font-size: 0.96rem;
                line-height: 1.55;
            }

            div[data-testid="stVerticalBlock"]:has(.if-simple-auth-card-marker):not(:has(div[data-testid="stVerticalBlock"] .if-simple-auth-card-marker)) [data-testid="stAlert"] {
                border-radius: 14px;
                border: 1px solid rgba(226, 232, 240, 0.92);
                background: rgba(248, 250, 252, 0.96);
                box-shadow: none;
            }

            div[data-testid="stVerticalBlock"]:has(.if-simple-auth-card-marker):not(:has(div[data-testid="stVerticalBlock"] .if-simple-auth-card-marker)) [data-testid="stTabs"] [role="tablist"],
            div[data-testid="stVerticalBlock"]:has(.if-simple-auth-card-marker):not(:has(div[data-testid="stVerticalBlock"] .if-simple-auth-card-marker)) .stTabs [data-baseweb="tab-list"] {
                margin-bottom: 1rem;
                gap: 0.5rem;
                justify-content: center;
                border: none;
                background: transparent;
                box-shadow: none;
                padding: 0;
            }

            div[data-testid="stVerticalBlock"]:has(.if-simple-auth-card-marker):not(:has(div[data-testid="stVerticalBlock"] .if-simple-auth-card-marker)) [data-testid="stTabs"] button[role="tab"],
            div[data-testid="stVerticalBlock"]:has(.if-simple-auth-card-marker):not(:has(div[data-testid="stVerticalBlock"] .if-simple-auth-card-marker)) .stTabs [data-baseweb="tab"] {
                min-height: 44px;
                min-width: 140px;
                border-radius: 999px;
                border: 1px solid rgba(203, 213, 225, 0.9);
                background: #ffffff;
                color: var(--muted) !important;
                font-weight: 700;
                box-shadow: none;
                transition: none;
                flex: 1 1 0;
            }

            div[data-testid="stVerticalBlock"]:has(.if-simple-auth-card-marker):not(:has(div[data-testid="stVerticalBlock"] .if-simple-auth-card-marker)) [data-testid="stTabs"] button[role="tab"]::after,
            div[data-testid="stVerticalBlock"]:has(.if-simple-auth-card-marker):not(:has(div[data-testid="stVerticalBlock"] .if-simple-auth-card-marker)) .stTabs [data-baseweb="tab"]::after {
                display: none;
            }

            div[data-testid="stVerticalBlock"]:has(.if-simple-auth-card-marker):not(:has(div[data-testid="stVerticalBlock"] .if-simple-auth-card-marker)) [data-testid="stTabs"] [aria-selected="true"],
            div[data-testid="stVerticalBlock"]:has(.if-simple-auth-card-marker):not(:has(div[data-testid="stVerticalBlock"] .if-simple-auth-card-marker)) .stTabs [aria-selected="true"] {
                color: var(--text) !important;
                border-color: rgba(148, 163, 184, 0.95);
                background: rgba(241, 245, 249, 0.96);
                box-shadow: none;
            }

            div[data-testid="stVerticalBlock"]:has(.if-simple-auth-card-marker):not(:has(div[data-testid="stVerticalBlock"] .if-simple-auth-card-marker)) [data-testid="stTabs"] [role="tabpanel"] {
                padding: 0;
                border: none;
                background: transparent;
                box-shadow: none;
            }

            .if-simple-auth-section {
                margin-bottom: 0.9rem;
            }

            .if-simple-auth-section-title {
                color: var(--text2) !important;
                font-family: "Outfit", sans-serif !important;
                font-size: 1.1rem;
                font-weight: 700;
                line-height: 1.2;
            }

            .if-simple-auth-section-copy {
                margin-top: 0.3rem;
                color: var(--muted) !important;
                font-size: 0.9rem;
                line-height: 1.5;
            }

            div[data-testid="stVerticalBlock"]:has(.if-simple-auth-card-marker):not(:has(div[data-testid="stVerticalBlock"] .if-simple-auth-card-marker)) [data-testid="stForm"] {
                border: none;
                background: transparent;
                padding: 0;
            }

            div[data-testid="stVerticalBlock"]:has(.if-simple-auth-card-marker):not(:has(div[data-testid="stVerticalBlock"] .if-simple-auth-card-marker)) [data-testid="stTextInput"] {
                margin-bottom: 0.85rem;
            }

            div[data-testid="stVerticalBlock"]:has(.if-simple-auth-card-marker):not(:has(div[data-testid="stVerticalBlock"] .if-simple-auth-card-marker)) .stTextInput input {
                min-height: 48px;
                border-radius: 12px !important;
                border: 1px solid rgba(203, 213, 225, 0.95) !important;
                background: #ffffff !important;
                box-shadow: none !important;
                padding-left: 0.9rem !important;
                color: #0f172a !important;
            }

            div[data-testid="stVerticalBlock"]:has(.if-simple-auth-card-marker):not(:has(div[data-testid="stVerticalBlock"] .if-simple-auth-card-marker)) .stTextInput input:focus {
                border-color: rgba(67, 97, 238, 0.45) !important;
                box-shadow: 0 0 0 3px rgba(67, 97, 238, 0.12) !important;
            }

            div[data-testid="stVerticalBlock"]:has(.if-simple-auth-card-marker):not(:has(div[data-testid="stVerticalBlock"] .if-simple-auth-card-marker)) .stFormSubmitButton > button {
                min-height: 48px;
                border-radius: 12px;
                border: none !important;
                font-family: "Outfit", sans-serif !important;
                font-size: 1rem;
                font-weight: 700;
                color: #ffffff !important;
                background: var(--blue) !important;
                box-shadow: none;
            }

            .if-simple-auth-note {
                margin-top: 0.75rem;
                color: var(--light) !important;
                font-size: 0.84rem;
                text-align: center;
            }

            @media (max-width: 780px) {
                .main .block-container:has(.if-simple-auth-screen) {
                    max-width: 100%;
                    min-height: auto;
                    padding-top: 0.8rem;
                    padding-bottom: 0.8rem;
                }

                div[data-testid="stVerticalBlock"]:has(.if-simple-auth-card-marker):not(:has(div[data-testid="stVerticalBlock"] .if-simple-auth-card-marker)) {
                    padding: 1rem;
                    border-radius: 18px;
                }

                .if-simple-auth-title {
                    font-size: 1.7rem;
                }
            }
            </style>
            <div class="if-simple-auth-screen"></div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown('<div class="if-simple-auth-card-marker"></div>', unsafe_allow_html=True)
        st.markdown(
            """
            <div class="if-simple-auth-head">
              <div class="if-simple-auth-title">Sign in</div>
              <div class="if-simple-auth-copy">
                Access your invoice workspace with a simpler login screen.
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.session_state.get("auth_notice"):
            st.info(st.session_state.auth_notice)

        sign_in_tab, register_tab = st.tabs(["Sign In", "Create Account"])
        with sign_in_tab:
            st.markdown(
                """
                <div class="if-simple-auth-section">
                  <div class="if-simple-auth-section-title">Welcome back</div>
                  <div class="if-simple-auth-section-copy">
                    Enter your email and password to continue.
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            with st.form("login_form"):
                email = st.text_input(
                    "Email",
                    key="login_email",
                    placeholder="you@example.com",
                )
                password = st.text_input(
                    "Password",
                    type="password",
                    key="login_password",
                    placeholder="Enter your password",
                )
                submitted = st.form_submit_button("Sign In", type="primary", use_container_width=True)
            if submitted:
                error = authenticate_user(email, password)
                if error:
                    st.error(error)
                else:
                    st.rerun()

        with register_tab:
            st.markdown(
                """
                <div class="if-simple-auth-section">
                  <div class="if-simple-auth-section-title">Create an account</div>
                  <div class="if-simple-auth-section-copy">
                    Set up your profile and start using the workspace.
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            with st.form("register_form"):
                full_name = st.text_input(
                    "Full Name",
                    key="register_full_name",
                    placeholder="Your name",
                )
                company = st.text_input(
                    "Company",
                    key="register_company",
                    placeholder="Company name",
                )
                email = st.text_input(
                    "Email",
                    key="register_email",
                    placeholder="you@example.com",
                )
                password = st.text_input(
                    "Password",
                    type="password",
                    key="register_password",
                    placeholder="Create a password",
                )
                confirm_password = st.text_input(
                    "Confirm Password",
                    type="password",
                    key="register_password_confirm",
                    placeholder="Re-enter your password",
                )
                submitted = st.form_submit_button("Create Account", type="primary", use_container_width=True)
            if submitted:
                error = register_user(full_name, company, email, password, confirm_password)
                if error:
                    st.error(error)
                else:
                    st.success("Account created and signed in.")
                    st.rerun()
        st.markdown(
            """
            <div class="if-simple-auth-note">
              Session tokens stay limited to this browser session.
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_session_bar():
    user = st.session_state.get("auth_user") or {}
    name = user.get("full_name") or user.get("email") or "User"
    email = user.get("email") or ""
    company = user.get("company") or "-"
    role = str(user.get("role") or "user").upper()
    initials = "".join(part[:1] for part in name.split() if part)[:2].upper() or name[:2].upper() or "U"

    info_col, action_col = st.columns([5.2, 1], gap="small")
    with info_col:
        st.markdown(
            f"""
            <div class="if-user-strip if-reveal">
              <div class="if-user-avatar">{html.escape(initials)}</div>
              <div class="if-user-copy">
                <div class="if-user-title">Signed in as {html.escape(name)}</div>
                <div class="if-user-meta">
                  <span class="if-user-chip presence">Active session</span>
                  <span class="if-user-chip">{html.escape(email or "No email")}</span>
                  <span class="if-user-chip">{html.escape(company)}</span>
                  <span class="if-user-chip role">{html.escape(role)}</span>
                </div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with action_col:
        if st.button("Log out", width='stretch', key="logout_btn"):
            clear_auth_state("You signed out.")
            st.rerun()


def port_in_use(host: str, port: int, timeout: float = 0.4) -> bool:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(timeout)
            return sock.connect_ex((host, port)) == 0
    except OSError:
        return False


def backend_usable_without_auth(port: int) -> bool:
    base = f"http://127.0.0.1:{port}"
    try:
        health = requests.get(f"{base}/health", timeout=0.35)
        return health.status_code == 200
    except RequestException:
        return False


def select_backend_port() -> int:
    preferred_ports = [8000, 8001, 8002, 8003, 8010, 8020]
    managed_proc = st.session_state.get("backend_proc")
    if managed_proc is not None and managed_proc.poll() is None:
        managed_port = int(st.session_state.get("backend_port", 8000))
        if backend_usable_without_auth(managed_port):
            return managed_port

    # Reuse an already healthy local backend before launching a new one.
    for port in preferred_ports:
        if port_in_use("127.0.0.1", port) and backend_usable_without_auth(port):
            return port

    for port in preferred_ports:
        if not port_in_use("127.0.0.1", port):
            return port

    return 8000


def sync_backend_endpoint():
    selected_port = select_backend_port()
    selected_base = f"http://127.0.0.1:{selected_port}/api"
    if (
        st.session_state.get("backend_port") != selected_port
        or st.session_state.get("base_url") != selected_base
    ):
        st.session_state.backend_port = selected_port
        st.session_state.base_url = selected_base
        st.session_state.backend_autostart_attempted = False


def swap_url_base(url: str, old_base: str, new_base: str) -> str:
    if old_base and url.startswith(old_base):
        return f"{new_base}{url[len(old_base):]}"
    return url


def root_url(base_url: str) -> str:
    return base_url[:-4] if base_url.endswith("/api") else base_url


def set_backend_health(ok: bool, status: str) -> Tuple[bool, str]:
    st.session_state.backend_ok = ok
    st.session_state.backend_status = status
    st.session_state.backend_health_checked_at = time.time()
    st.session_state.backend_health_base_url = st.session_state.base_url
    return ok, status


def build_erp_launch_url(invoice_id: Optional[str] = None) -> str:
    params = {"backend_api": st.session_state.base_url}
    if invoice_id:
        params["invoice_id"] = invoice_id
    return f"{st.session_state.erp_url.rstrip('/')}?{urlencode(params)}"


def check_erp_module(base_url: Optional[str] = None, timeout: float = 3.0) -> Tuple[bool, str]:
    erp_base = (base_url or st.session_state.erp_url).rstrip("/")
    candidates = [f"{erp_base}/_stcore/health", f"{erp_base}/healthz", erp_base]
    last_error = "ERP module is offline."
    for url in candidates:
        try:
            res = requests.get(url, timeout=timeout)
            if res.status_code == 200:
                return True, "ready"
            last_error = f"status {res.status_code}"
        except RequestException as exc:
            last_error = str(exc)
    return False, last_error


def erp_launch_host_is_local() -> bool:
    parsed = urlparse(st.session_state.erp_url)
    return (parsed.hostname or "").lower() in {"127.0.0.1", "localhost", "::1"}


def erp_launch_port() -> int:
    parsed = urlparse(st.session_state.erp_url)
    if parsed.port is not None:
        return int(parsed.port)
    return 443 if parsed.scheme == "https" else 80


def start_erp_process() -> Tuple[bool, str]:
    ready, _ = check_erp_module(timeout=1.0)
    if ready:
        return True, "ERP module already running."

    if not erp_launch_host_is_local():
        return False, f"ERP module is offline at {st.session_state.erp_url}."

    port = erp_launch_port()
    managed_proc = st.session_state.get("erp_proc")
    if managed_proc is not None and managed_proc.poll() is None:
        return True, f"ERP process already starting on port {port}."

    if port_in_use("127.0.0.1", port):
        return False, f"Port {port} is already in use, but the ERP module is not responding."

    try:
        cmd = [
            sys.executable,
            "-m",
            "streamlit",
            "run",
            "erp_frontend.py",
            "--server.port",
            str(port),
            "--server.headless",
            "true",
        ]
        proc = subprocess.Popen(cmd, cwd=".")
        st.session_state.erp_proc = proc
        st.session_state.erp_started_at = time.time()
        return True, f"ERP module starting on port {port}."
    except Exception as exc:
        return False, f"Failed to start ERP module: {exc}"


def ensure_erp_module_ready(timeout: float = 25.0) -> Tuple[bool, str]:
    ready, status = check_erp_module(timeout=1.0)
    if ready:
        return True, status

    started, start_status = start_erp_process()
    if not started:
        return False, start_status

    last_status = start_status
    for _ in range(max(1, int(timeout))):
        time.sleep(1.0)
        ready, last_status = check_erp_module(timeout=1.5)
        if ready:
            return True, "ready"

        managed_proc = st.session_state.get("erp_proc")
        if managed_proc is not None and managed_proc.poll() is not None:
            return False, f"ERP module stopped before it became ready (exit code {managed_proc.poll()})."

    return False, f"ERP module did not become ready at {st.session_state.erp_url}. Last status: {last_status}"


def open_url_in_browser(url: str, new_tab: bool = True) -> bool:
    try:
        if new_tab:
            return bool(webbrowser.open_new_tab(url))
        return bool(webbrowser.open(url))
    except Exception:
        return False


def check_backend(base_url: str, timeout: float = 1.5) -> Tuple[bool, str]:
    base = root_url(base_url)
    parsed = urlparse(base)
    hostname = (parsed.hostname or "").lower()
    port = parsed.port or (443 if parsed.scheme == "https" else 80)

    if hostname in {"127.0.0.1", "localhost"} and not port_in_use("127.0.0.1", port, timeout=0.15):
        return False, f"port {port} is closed"

    try:
        res = requests.get(f"{base}/health", timeout=timeout)
        if res.status_code == 200:
            return True, "healthy"
        return False, f"status {res.status_code}"
    except RequestException as e:
        return False, str(e)


def refresh_backend_health(force: bool = False, timeout: float = 1.5) -> Tuple[bool, str]:
    now = time.time()
    cached_base = st.session_state.get("backend_health_base_url")
    cached_at = float(st.session_state.get("backend_health_checked_at") or 0.0)
    if (
        not force
        and cached_base == st.session_state.base_url
        and now - cached_at < 2.0
    ):
        return (
            bool(st.session_state.get("backend_ok", False)),
            str(st.session_state.get("backend_status") or "unknown"),
        )

    ok, status = check_backend(st.session_state.base_url, timeout=timeout)
    return set_backend_health(ok, status)

def start_backend_process() -> Tuple[bool, str]:
    try:
        if st.session_state.backend_proc and st.session_state.backend_proc.poll() is None:
            return True, "Backend process already running."
        cmd = [
            sys.executable,
            "-m",
            "uvicorn",
            "backend.app.main:app",
            "--host",
            "0.0.0.0",
            "--port",
            str(st.session_state.backend_port),
        ]
        proc = subprocess.Popen(cmd, cwd=".")
        st.session_state.backend_proc = proc
        st.session_state.backend_started_at = time.time()
        return True, f"Backend process started on port {st.session_state.backend_port}."
    except Exception as e:
        return False, f"Failed to start backend: {e}"

def auto_start_backend(wait_timeout: float = 12.0, poll_interval: float = 0.35) -> Tuple[bool, str]:
    if st.session_state.backend_autostart_attempted:
        return (
            bool(st.session_state.get("backend_ok", False)),
            str(st.session_state.get("backend_status") or "Startup already attempted."),
        )
    st.session_state.backend_autostart_attempted = True
    ok, start_status = start_backend_process()
    if not ok:
        return set_backend_health(False, start_status)

    port = int(st.session_state.backend_port)
    deadline = time.time() + wait_timeout
    last_status = start_status
    while time.time() < deadline:
        managed_proc = st.session_state.get("backend_proc")
        if managed_proc is not None and managed_proc.poll() is not None:
            return set_backend_health(
                False,
                f"Backend stopped before it became ready (exit code {managed_proc.poll()}).",
            )

        if port_in_use("127.0.0.1", port, timeout=0.12):
            ok, last_status = check_backend(st.session_state.base_url, timeout=0.75)
            if ok:
                return set_backend_health(True, last_status)

        time.sleep(poll_interval)

    return set_backend_health(
        False,
        f"Backend did not become ready within {wait_timeout:.0f}s. Last status: {last_status}",
    )


def post_json(url: str, payload: Optional[dict] = None, use_auth: bool = True, timeout: float = 15.0):
    headers = {}
    if use_auth:
        headers.update(api_headers())
    try:
        if payload is None:
            response = requests.post(url, headers=headers, timeout=timeout)
            handle_api_auth_failure(response, use_auth=use_auth)
            return response
        headers["Content-Type"] = "application/json"
        response = requests.post(url, json=payload, headers=headers, timeout=timeout)
        handle_api_auth_failure(response, use_auth=use_auth)
        return response
    except RequestException as e:
        original_base = st.session_state.base_url
        sync_backend_endpoint()
        fallback_base = st.session_state.base_url
        if fallback_base != original_base:
            retry_url = swap_url_base(url, original_base, fallback_base)
            try:
                if payload is None:
                    response = requests.post(retry_url, headers=headers, timeout=timeout)
                    handle_api_auth_failure(response, use_auth=use_auth)
                    return response
                response = requests.post(retry_url, json=payload, headers=headers, timeout=timeout)
                handle_api_auth_failure(response, use_auth=use_auth)
                return response
            except RequestException as retry_error:
                return {"_error": f"Backend offline. Start it at {fallback_base}. Details: {retry_error}"}
        return {"_error": f"Backend offline. Start it at {st.session_state.base_url}. Details: {e}"}


def get_json(url: str, timeout: float = 15.0, use_auth: bool = True):
    headers = api_headers() if use_auth else {}
    try:
        response = requests.get(url, headers=headers, timeout=timeout)
        handle_api_auth_failure(response, use_auth=use_auth)
        return response
    except RequestException as e:
        original_base = st.session_state.base_url
        sync_backend_endpoint()
        fallback_base = st.session_state.base_url
        if fallback_base != original_base:
            retry_url = swap_url_base(url, original_base, fallback_base)
            try:
                response = requests.get(retry_url, headers=headers, timeout=timeout)
                handle_api_auth_failure(response, use_auth=use_auth)
                return response
            except RequestException as retry_error:
                return {"_error": f"Backend offline. Start it at {fallback_base}. Details: {retry_error}"}
        return {"_error": f"Backend offline. Start it at {st.session_state.base_url}. Details: {e}"}


def upload_single_file(base_url: str, filename: str, content: bytes, content_type: str):
    files = {"files": (filename, content, content_type)}
    try:
        response = requests.post(f"{base_url}/invoices/upload", headers=api_headers(), files=files, timeout=60)
        handle_api_auth_failure(response)
        return response
    except RequestException as e:
        original_base = base_url
        sync_backend_endpoint()
        fallback_base = st.session_state.base_url
        if fallback_base != original_base:
            try:
                response = requests.post(
                    f"{fallback_base}/invoices/upload",
                    headers=api_headers(),
                    files=files,
                    timeout=60,
                )
                handle_api_auth_failure(response)
                return response
            except RequestException as retry_error:
                return {"_error": f"Backend offline. Start it at {fallback_base}. Details: {retry_error}"}
        return {"_error": f"Backend offline. Start it at {st.session_state.base_url}. Details: {e}"}


def build_files_from_zip(zip_bytes: bytes) -> List[Tuple[str, bytes, str]]:
    results = []
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        for info in zf.infolist():
            if info.is_dir():
                continue
            name = info.filename.split("/")[-1].strip()
            if not name:
                continue
            content = zf.read(info)
            mime = mimetypes.guess_type(name)[0] or "application/octet-stream"
            results.append((name, content, mime))
    return results


def render_upload():
    render_section_intro(
        "Upload Invoices",
        "Add single files or zip folders. Processing starts automatically after upload.",
    )
    st.markdown(
        """
        <div class="if-upload-shell if-reveal">
          <div class="if-upload-head">
            <div class="if-upload-title">Upload Invoices</div>
            <div class="if-upload-sub">Batch files or zip folders. OCR extraction starts immediately.</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    left_col, right_col = st.columns([2, 1], gap="large")
    auto_process = True
    results: Optional[List[Dict[str, Any]]] = None

    with left_col:
        selector_col, hint_col = st.columns([2, 1], gap="small")
        with selector_col:
            mode = st.radio("Upload Mode", ["Batch files", "Folder (zip)"], horizontal=True, key="upload_mode")
        with hint_col:
            st.caption("Supported: PDF, PNG, JPG, JPEG, TIF, TIFF, ZIP")
            st.caption("Production mode: auto-process ON")

        use_cache = st.checkbox("Use cache for processing", value=True, key="upload_use_cache")
        prefer_handwriting_ocr = st.checkbox(
            "Prefer handwritten OCR for this batch",
            value=False,
            key="upload_prefer_handwriting_ocr",
            help="Use this only for basic handwritten invoices. Printed invoices should usually leave this off.",
        )

        if mode == "Batch files":
            files = st.file_uploader(
                "Select invoice files",
                type=["pdf", "png", "jpg", "jpeg", "tif", "tiff"],
                accept_multiple_files=True,
                key="upload_batch_files",
            )
            clicked = st.button("Upload Selected Files", width='stretch', type="primary", key="upload_batch_button")
            if clicked:
                if not files:
                    st.warning("Please select at least one file.")
                else:
                    entries = [(f.name, f.getvalue(), f.type or "application/octet-stream") for f in files]
                    results = upload_invoice_entries(
                        entries,
                        auto_process=auto_process,
                        use_cache=use_cache,
                        prefer_handwriting_ocr=prefer_handwriting_ocr,
                    )
        else:
            zip_file = st.file_uploader(
                "Upload a zip file containing invoices",
                type=["zip"],
                key="upload_zip_file",
            )
            clicked = st.button("Upload Zip Contents", width='stretch', type="primary", key="upload_zip_button")
            if clicked:
                if not zip_file:
                    st.warning("Please select a zip file.")
                else:
                    try:
                        extracted = build_files_from_zip(zip_file.getvalue())
                    except Exception as e:
                        st.error(f"Failed to read zip: {e}")
                        extracted = []
                    if not extracted:
                        st.warning("No files found in zip.")
                    else:
                        results = upload_invoice_entries(
                            extracted,
                            auto_process=auto_process,
                            use_cache=use_cache,
                            prefer_handwriting_ocr=prefer_handwriting_ocr,
                        )

    with right_col:
        render_recent_upload_panel()

    if results:
        render_upload_results(results, auto_process=auto_process)
        active_invoice = st.session_state.get("active_invoice_id")
        if active_invoice:
            loaded, _ = load_review_details_for_invoice(active_invoice)
            if loaded:
                st.success(f"Review data is ready for invoice {active_invoice}.")
            else:
                st.info("Review data will appear automatically in Review once processing completes.")


def render_processing():
    render_section_intro(
        "Processing",
        "Start extraction for any invoice and monitor progress in real time.",
    )
    st.caption("Use the invoice ID returned in Upload to start or check processing.")

    invoice_id = st.text_input("Invoice ID", key="process_id", placeholder="Enter invoice ID")
    use_cache = st.checkbox("Use cache when available", value=True, key="process_cache")
    prefer_handwriting_ocr = st.checkbox(
        "Prefer handwritten OCR",
        value=False,
        key="process_prefer_handwriting_ocr",
        help="Turn this on only for simple handwritten invoices. Default processing remains best for printed invoices.",
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Start Processing", width='stretch', type="primary", key="start_processing_btn"):
            if not invoice_id:
                st.warning("Please enter an invoice ID.")
                return
            payload = {
                "invoice_id": invoice_id,
                "use_cache": use_cache,
                "prefer_handwriting_ocr": prefer_handwriting_ocr,
            }
            res = post_json(f"{st.session_state.base_url}/process/start", payload)
            if isinstance(res, dict) and res.get("_error"):
                st.error(f"Backend not reachable: {res['_error']}")
                return
            data = ensure_dict_payload(response_payload(res))
            if res.status_code == 200:
                st.success(data.get("message", "Processing started"))
                st.session_state.process_status = data
            else:
                st.error(data)
    with col2:
        if st.button("Check Status", width='stretch', key="check_processing_btn"):
            if not invoice_id:
                st.warning("Please enter an invoice ID.")
                return
            res = get_json(f"{st.session_state.base_url}/process/status/{invoice_id}")
            if isinstance(res, dict) and res.get("_error"):
                st.error(f"Backend not reachable: {res['_error']}")
                return
            data = ensure_dict_payload(response_payload(res))
            if res.status_code == 200:
                st.session_state.process_status = data
            else:
                st.error(data)
    with col3:
        if st.button("Clear Status", width='stretch', key="clear_processing_btn"):
            st.session_state.process_status = None

    status = st.session_state.process_status
    if not status:
        st.info("No processing status yet. Start processing or check an existing invoice.")
        return

    raw_progress = status.get("progress", 0)
    progress_value = raw_progress if isinstance(raw_progress, (int, float)) else 0
    clamped_progress = max(0.0, min(progress_value / 100, 1.0))
    st.progress(clamped_progress)

    metric_col1, metric_col2, metric_col3 = st.columns(3)
    metric_col1.metric("Progress", f"{progress_value:.0f}%")
    metric_col2.metric("Status", str(status.get("status", "unknown")).upper())
    metric_col3.metric("Current Step", str(status.get("current_step") or "-"))

    if status.get("error_message"):
        st.error(status.get("error_message"))

    if status.get("extracted_data"):
        with st.expander("View extracted data"):
            st.json(status.get("extracted_data"))


def render_review():
    render_section_intro(
        "Manual Review",
        "Review extracted invoice data automatically from your uploaded files.",
    )
    uploaded_ids = [invoice_id for invoice_id in reversed(st.session_state.last_uploads) if invoice_id]
    uploaded_ids = list(dict.fromkeys(uploaded_ids))
    if not uploaded_ids:
        st.info("Upload at least one invoice from the Upload tab to start review.")
        return

    active_invoice = st.session_state.get("active_invoice_id")
    if active_invoice not in uploaded_ids:
        active_invoice = uploaded_ids[0]
        set_active_invoice(active_invoice)

    selector_col, action_col1, action_col2 = st.columns([2, 1, 1])
    with selector_col:
        selected_invoice = st.selectbox(
            "Uploaded Invoice",
            uploaded_ids,
            index=uploaded_ids.index(active_invoice),
            key="review_invoice_selector",
        )

    if selected_invoice != st.session_state.active_invoice_id:
        set_active_invoice(selected_invoice)

    invoice_id = st.session_state.active_invoice_id
    cached_details = st.session_state.get("review_details")
    cached_status = (
        str(cached_details.get("processing_status") or "").lower()
        if isinstance(cached_details, dict)
        else ""
    )
    if (
        st.session_state.get("review_loaded_invoice_id") != invoice_id
        or cached_details is None
        or cached_status not in REVIEW_TERMINAL_STATUSES
    ):
        load_review_details_for_invoice(invoice_id)

    with action_col1:
        if st.button("Refresh Details", width='stretch', type="primary", key="refresh_review_btn"):
            load_review_details_for_invoice(invoice_id)
    with action_col2:
        if st.button("Clear Review", width='stretch', key="clear_review_btn"):
            st.session_state.review_details = None
            st.session_state.review_json = ""
            st.session_state.review_loaded_invoice_id = None
            st.session_state.review_load_error = None

    details = st.session_state.review_details
    if not details:
        st.info(f"Review data for invoice {invoice_id} is not ready yet.")
        last_error = st.session_state.get("review_load_error")
        can_auto_refresh = True
        if last_error:
            st.caption(f"Latest status: {last_error}")
            lowered_error = str(last_error).lower()
            if "not found" in lowered_error:
                can_auto_refresh = False
        st.checkbox("Auto refresh until ready", key="review_auto_refresh")
        if st.session_state.review_auto_refresh and can_auto_refresh:
            st.caption("Refreshing in 3 seconds...")
            time.sleep(3.0)
            st.rerun()
        return

    if not isinstance(details, dict):
        st.error("Unexpected review details format.")
        return

    if details.get("invoice_id") != invoice_id:
        st.info("Loaded details were stale. Refreshing for selected invoice.")
        load_review_details_for_invoice(invoice_id)
        return

    processing_status = str(details.get("processing_status") or "pending").lower()
    ready_for_review = bool(details.get("ready_for_review")) or processing_status in REVIEW_READY_STATUSES
    extracted_data = details.get("extracted_data") if isinstance(details.get("extracted_data"), dict) else {}
    confidence_scores = details.get("confidence_scores") if isinstance(details.get("confidence_scores"), dict) else {}

    meta_col1, meta_col2, meta_col3 = st.columns(3)
    meta_col1.metric("Filename", details.get("filename") or "-")
    meta_col2.metric("Processing Status", processing_status.upper())
    meta_col3.metric("Extracted Fields", len(extracted_data))

    if not ready_for_review:
        progress_value = int(details.get("progress") or 0)
        step_value = str(details.get("current_step") or "-")
        status_col1, status_col2, status_col3 = st.columns(3)
        status_col1.metric("Progress", f"{progress_value}%")
        status_col2.metric("Status", processing_status.upper())
        status_col3.metric("Current Step", step_value)
        if processing_status == "failed":
            st.error(details.get("error_message") or "Processing failed. Retry from the Processing tab.")
        else:
            st.info("Extraction is still running. Review fields will unlock automatically once completed.")
        st.checkbox("Auto refresh until ready", key="review_auto_refresh")
        if st.session_state.review_auto_refresh and processing_status in REVIEW_POLL_STATUSES:
            st.caption("Refreshing in 3 seconds...")
            time.sleep(3.0)
            st.rerun()
        return

    if confidence_scores:
        confidence_rows = []
        for field, payload in confidence_scores.items():
            confidence = payload.get("confidence") if isinstance(payload, dict) else payload
            if isinstance(confidence, (int, float)):
                if confidence <= 1:
                    confidence_text = f"{confidence * 100:.1f}%"
                else:
                    confidence_text = f"{confidence:.1f}%"
            else:
                confidence_text = str(confidence)
            confidence_rows.append({"Field": field, "Confidence": confidence_text})
        st.dataframe(confidence_rows, width='stretch')

    edited_json = st.text_area(
        "Extracted Data (JSON)",
        key="review_json",
        height=320,
        help="Edit values directly in JSON format before submitting.",
    )
    notes = st.text_area("Review Notes", key="review_notes", placeholder="Optional reviewer notes")
    approved = st.checkbox("Approve invoice", value=True, key="review_approved")

    if st.button("Submit Review", width='stretch', type="primary", key="submit_review_btn"):
        try:
            edited_data = json.loads(edited_json) if edited_json.strip() else {}
        except Exception as e:
            st.error(f"Invalid JSON: {e}")
            return

        corrections = []
        for key in set(extracted_data.keys()) | set(edited_data.keys()):
            original_value = extracted_data.get(key)
            corrected_value = edited_data.get(key)
            if corrected_value != original_value:
                confidence_entry = confidence_scores.get(key, {}) if isinstance(confidence_scores, dict) else {}
                corrections.append(
                    {
                        "field_name": key,
                        "original_value": original_value,
                        "corrected_value": corrected_value,
                        "confidence": confidence_entry.get("confidence") if isinstance(confidence_entry, dict) else None,
                    }
                )

        payload = {
            "invoice_id": invoice_id,
            "corrections": corrections,
            "notes": notes or None,
            "approved": approved,
        }
        res = post_json(f"{st.session_state.base_url}/review/{invoice_id}/submit", payload)
        if isinstance(res, dict) and res.get("_error"):
            st.error(f"Backend not reachable: {res['_error']}")
            return
        data = response_payload(res)
        if res.status_code == 200:
            st.success(f"Review submitted with {len(corrections)} correction(s).")
            with st.expander("View submission response"):
                st.json(data)
        else:
            st.error(data)


def render_export():
    render_section_intro(
        "Export",
        "Generate a downloadable output for a single invoice in JSON, CSV, or Excel format.",
    )
    if st.session_state.get("active_invoice_id") and not st.session_state.get("export_id"):
        st.session_state.export_id = st.session_state.active_invoice_id
    input_col, format_col = st.columns([2, 1])
    with input_col:
        invoice_id = st.text_input("Invoice ID", key="export_id", placeholder="Enter invoice ID")
    with format_col:
        export_format = st.selectbox(
            "Format",
            ["json", "csv", "excel"],
            key="export_format",
            format_func=lambda value: value.upper(),
        )
    target_invoice_id = invoice_id or st.session_state.get("active_invoice_id")
    erp_launch_url = build_erp_launch_url(target_invoice_id)

    erp_col1, erp_col2 = st.columns(2)
    with erp_col1:
        fill_erp_clicked = st.button("Fill in ERP", width='stretch', key="fill_erp_btn")
    with erp_col2:
        open_erp_clicked = st.button("Open ERP Module", width='stretch', key="open_erp_btn")

    erp_feedback = None
    erp_feedback_kind = None

    st.caption(
        "Open ERP Module will start the ERP page automatically on port 8503 if it is not already running."
    )

    if fill_erp_clicked:
        if not target_invoice_id:
            st.warning("Please enter an invoice ID before filling ERP.")
            return
        set_res = post_json(
            f"{st.session_state.base_url}/erp/set_current_invoice",
            {"invoice_id": target_invoice_id},
        )
        if isinstance(set_res, dict) and set_res.get("_error"):
            st.error(f"Backend not reachable: {set_res['_error']}")
            return
        set_data = response_payload(set_res)
        if getattr(set_res, "status_code", None) != 200:
            st.error(set_data)
            return
        st.success(f"Invoice {target_invoice_id} sent to ERP.")
        st.session_state.erp_launch_nonce += 1
        ready, status = ensure_erp_module_ready()
        if not ready:
            st.error(status)
            st.caption("Manual fallback: `streamlit run erp_frontend.py --server.port 8503`")
            return
        launch_url = build_erp_launch_url(target_invoice_id)
        st.session_state.erp_ready_url = launch_url
        opened = open_url_in_browser(launch_url, new_tab=True)
        if opened:
            erp_feedback = "ERP module opened in a new browser tab."
            erp_feedback_kind = "success"
        else:
            erp_feedback = "ERP module is ready. Use the link below if your browser did not open it automatically."
            erp_feedback_kind = "info"

    if open_erp_clicked:
        ready, status = ensure_erp_module_ready()
        if not ready:
            st.error(status)
            st.caption("Manual fallback: `streamlit run erp_frontend.py --server.port 8503`")
            return
        st.session_state.erp_ready_url = erp_launch_url
        opened = open_url_in_browser(erp_launch_url, new_tab=True)
        if opened:
            erp_feedback = "ERP module opened in a new browser tab."
            erp_feedback_kind = "success"
        else:
            erp_feedback = "ERP module is ready. Use the link below if your browser did not open it automatically."
            erp_feedback_kind = "info"

    if erp_feedback_kind == "success":
        st.success(erp_feedback)
    elif erp_feedback_kind == "info":
        st.info(erp_feedback)

    ready_launch_url = st.session_state.get("erp_ready_url")
    if ready_launch_url:
        st.link_button("Open ERP Page", ready_launch_url, use_container_width=True)

    if st.button("Generate Export", width='stretch', type="primary", key="export_btn"):
        if not invoice_id:
            st.warning("Please enter an invoice ID.")
            return
        url = f"{st.session_state.base_url}/export/single/{invoice_id}?format={export_format}"
        res = post_json(url)
        if isinstance(res, dict) and res.get("_error"):
            st.error(f"Backend not reachable: {res['_error']}")
            return
        if export_format == "json":
            data = response_payload(res)
            if res.status_code != 200:
                st.error(data)
                return
            payload = data.get("data", data) if isinstance(data, dict) else data
            try:
                pretty = json.dumps(payload, indent=2)
            except TypeError:
                pretty = json.dumps({"data": str(payload)}, indent=2)
            st.success("JSON export ready.")
            st.code(pretty, language="json")
            st.download_button(
                "Download JSON",
                data=pretty,
                file_name=f"{invoice_id}.json",
                mime="application/json",
                key="download_json_btn",
            )
        else:
            if res.status_code != 200:
                st.error(response_payload(res))
                return
            st.success(f"{export_format.upper()} export ready.")
            if export_format == "csv":
                st.download_button(
                    "Download CSV",
                    data=res.content,
                    file_name=f"{invoice_id}.csv",
                    mime="text/csv",
                    key="download_csv_btn",
                )
            else:
                st.download_button(
                    "Download Excel",
                    data=res.content,
                    file_name=f"{invoice_id}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key="download_excel_btn",
                )


def render_history():
    render_section_intro(
        "History & Uploaded Files",
        "Refresh and filter invoice records to quickly find earlier uploads.",
    )
    if st.button("Refresh History", width='stretch', type="primary", key="refresh_history_btn"):
        res = get_json(f"{st.session_state.base_url}/invoices/list")
        if isinstance(res, dict) and res.get("_error"):
            st.error(f"Backend not reachable: {res['_error']}")
            return
        data = response_payload(res)
        if res.status_code == 200:
            st.session_state.history = data if isinstance(data, list) else []
        else:
            st.error(data)
            
            return

    history = st.session_state.history or []
    if not history:
        st.info("No history loaded yet. Click Refresh History.")
        return

    normalized_rows = [row if isinstance(row, dict) else {"value": row} for row in history]
    status_options = sorted(
        {
            str(row.get("processing_status") or row.get("status") or "unknown")
            for row in normalized_rows
        }
    )

    filter_col1, filter_col2 = st.columns([2, 1])
    with filter_col1:
        query = st.text_input("Search", key="history_search", placeholder="Invoice ID or filename")
    with filter_col2:
        selected_status = st.selectbox(
            "Status",
            ["All"] + status_options,
            key="history_status_filter",
        )

    query_text = query.strip().lower()
    filtered_rows = []
    for row in normalized_rows:
        row_status = str(row.get("processing_status") or row.get("status") or "unknown")
        if selected_status != "All" and row_status != selected_status:
            continue
        if query_text:
            haystack = " ".join(
                str(row.get(field, ""))
                for field in ("invoice_id", "filename", "processing_status", "status")
            ).lower()
            if query_text not in haystack:
                continue
        filtered_rows.append(row)

    st.caption(f"Showing {len(filtered_rows)} of {len(normalized_rows)} records.")
    st.dataframe(filtered_rows, width='stretch')


def main():
    st.set_page_config(page_title="invoiceflow", layout="wide", initial_sidebar_state="collapsed")
    init_state()
    apply_futuristic_theme()
    render_live_background()

    backend_ok, backend_status = refresh_backend_health(force=True)
    if not backend_ok:
        backend_ok, backend_status = auto_start_backend()

    if not st.session_state.get("backend_ok", False):
        inject_motion_runtime()
        st.error(f"Backend is offline. Start it at {st.session_state.base_url} and try again.")
        st.caption(f"Run: uvicorn backend.app.main:app --reload --port {st.session_state.backend_port}")
        st.caption(f"Details: {st.session_state.get('backend_status')}")
        return

    if not ensure_authenticated_user():
        render_auth_gate()
        inject_motion_runtime()
        return

    render_session_bar()
    render_main_header()
    render_capability_cards()
    render_dashboard_panel(st.session_state.backend_ok, st.session_state.backend_status)
    tabs = st.tabs(["Upload", "Review", "Export"])
    with tabs[0]:
        render_upload()
    with tabs[1]:
        render_review()
    with tabs[2]:
        render_export()

    inject_motion_runtime()


if __name__ == "__main__":
    main()


