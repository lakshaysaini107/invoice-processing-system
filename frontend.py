import html
import io
import json
import mimetypes
import subprocess
import sys
import time
import zipfile
from typing import Any, Dict, List, Optional, Tuple

import requests
from requests.exceptions import RequestException
import streamlit as st


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
        }

        [data-testid="stAppViewContainer"] {
            position: relative;
            overflow-x: hidden;
            background:
                radial-gradient(760px 320px at -10% -8%, rgba(245, 158, 11, 0.16), transparent 65%),
                radial-gradient(640px 290px at 105% 10%, rgba(45, 212, 191, 0.20), transparent 64%),
                radial-gradient(560px 280px at 35% 98%, rgba(251, 113, 133, 0.16), transparent 62%),
                var(--bg);
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
            padding-bottom: 2.2rem;
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
            border-radius: 16px;
            background: var(--glass2);
            padding: 0.75rem 1rem;
            margin-bottom: 0.85rem;
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 10px;
            box-shadow: 0 8px 24px rgba(67, 97, 238, 0.08);
        }

        .if-topbar::before {
            content: "";
            position: absolute;
            top: -80%;
            left: -22%;
            width: 22%;
            height: 260%;
            background: linear-gradient(
                90deg,
                rgba(255, 255, 255, 0),
                rgba(255, 255, 255, 0.55),
                rgba(255, 255, 255, 0)
            );
            transform: translateX(-180%) rotate(18deg);
            animation: ifTopbarBeam 9s linear infinite;
            pointer-events: none;
        }

        .if-brand {
            display: flex;
            align-items: center;
            gap: 10px;
            position: relative;
            z-index: 1;
        }

        .if-gem {
            position: relative;
            overflow: hidden;
            width: 40px;
            height: 40px;
            border-radius: 12px;
            background: linear-gradient(135deg, var(--blue), var(--indigo) 55%, var(--violet));
            display: flex;
            align-items: center;
            justify-content: center;
            color: #fff;
            box-shadow: 0 8px 22px rgba(123, 47, 247, 0.35);
            font-size: 1rem;
            font-weight: 700;
            animation: ifGemBob 4s ease-in-out infinite, ifGemGlow 3.5s ease-in-out infinite;
        }

        .if-gem::after {
            content: "";
            position: absolute;
            inset: -40% auto -40% -120%;
            width: 70%;
            background: linear-gradient(
                90deg,
                rgba(255, 255, 255, 0),
                rgba(255, 255, 255, 0.9),
                rgba(255, 255, 255, 0)
            );
            transform: skewX(-18deg);
            animation: ifGemSweep 4.4s ease-in-out infinite;
            pointer-events: none;
        }

        .if-brand-title {
            font-family: "Outfit", sans-serif !important;
            font-size: 1.08rem;
            font-weight: 800;
            line-height: 1;
            background: linear-gradient(135deg, var(--blue), var(--indigo), var(--violet));
            background-size: 220% 220%;
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            animation: ifBrandShift 6s ease-in-out infinite;
        }

        .if-brand-sub {
            font-size: 0.74rem;
            font-family: "JetBrains Mono", monospace !important;
            color: var(--muted) !important;
            margin-top: 2px;
            animation: ifSubPulse 3.2s ease-in-out infinite;
        }

        .if-status {
            border: 1px solid rgba(6, 214, 160, 0.35);
            color: #059669 !important;
            background: rgba(6, 214, 160, 0.08);
            border-radius: 999px;
            padding: 0.3rem 0.7rem;
            font-size: 0.72rem;
            font-weight: 700;
            font-family: "JetBrains Mono", monospace !important;
            animation: ifStatusPulse 2.8s ease-in-out infinite;
        }

        .if-hero {
            border: 1px solid var(--border2);
            border-radius: 22px;
            background: linear-gradient(160deg, rgba(255, 255, 255, 0.72), rgba(240, 244, 255, 0.48));
            text-align: center;
            padding: 2.1rem 1rem 1.5rem;
            margin-bottom: 1rem;
            box-shadow: var(--sh);
        }

        .if-hero-gem {
            width: 72px;
            height: 72px;
            border-radius: 22px;
            margin: 0 auto 0.8rem;
            background: linear-gradient(135deg, var(--blue), var(--indigo) 50%, var(--violet));
            display: flex;
            align-items: center;
            justify-content: center;
            color: #fff;
            font-size: 1.65rem;
            box-shadow: 0 16px 42px rgba(123, 47, 247, 0.35);
        }

        .if-hero-title {
            font-family: "Outfit", sans-serif !important;
            font-size: clamp(2rem, 4vw, 2.8rem);
            font-weight: 900;
            letter-spacing: -0.04em;
            line-height: 1.02;
            background: linear-gradient(135deg, var(--blue), var(--indigo), var(--violet), var(--rose));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }

        .if-hero-sub {
            max-width: 760px;
            margin: 0.5rem auto 0;
            color: var(--muted) !important;
            font-size: 0.96rem;
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
        }

        .if-cap-head {
            position: relative;
            display: flex;
            align-items: center;
            gap: 12px;
            margin: 0.2rem 0 0.65rem;
        }

        .if-cap-head::after {
            content: "";
            position: absolute;
            left: 0;
            bottom: -8px;
            width: 120px;
            height: 3px;
            border-radius: 99px;
            background: linear-gradient(90deg, var(--blue), var(--indigo), var(--teal));
            background-size: 200% 100%;
            animation: ifBrandShift 4s linear infinite;
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
            perspective: 900px;
        }

        .if-cap-card {
            position: relative;
            overflow: hidden;
            --card-delay: 0s;
            border: 1px solid var(--border2);
            border-radius: 18px;
            background: var(--glass);
            padding: 0.95rem;
            box-shadow: var(--sh);
            transition: box-shadow 0.25s ease, border-color 0.25s ease;
            animation: ifCapReveal 0.65s ease-out both, ifCapFloat 7s ease-in-out infinite;
            animation-delay: var(--card-delay), calc(1s + var(--card-delay));
        }

        .if-cap-card::before {
            content: "";
            position: absolute;
            top: -35%;
            left: -45%;
            width: 35%;
            height: 170%;
            background: linear-gradient(
                90deg,
                rgba(255, 255, 255, 0),
                rgba(255, 255, 255, 0.45),
                rgba(255, 255, 255, 0)
            );
            transform: translateX(-180%) rotate(18deg);
            animation: ifCapShine 8s ease-in-out infinite;
            animation-delay: calc(1.8s + var(--card-delay));
            pointer-events: none;
        }

        .if-cap-card:hover {
            border-color: rgba(67, 97, 238, 0.35);
            box-shadow: 0 18px 36px rgba(67, 97, 238, 0.18);
        }

        .if-cap-card:nth-child(1) { --card-delay: 0.02s; }
        .if-cap-card:nth-child(2) { --card-delay: 0.10s; }
        .if-cap-card:nth-child(3) { --card-delay: 0.18s; }
        .if-cap-card:nth-child(4) { --card-delay: 0.26s; }
        .if-cap-card:nth-child(5) { --card-delay: 0.34s; }
        .if-cap-card:nth-child(6) { --card-delay: 0.42s; }

        .if-cap-icon {
            width: 34px;
            height: 34px;
            border-radius: 10px;
            background: linear-gradient(135deg, rgba(67, 97, 238, 0.14), rgba(123, 47, 247, 0.10));
            display: flex;
            align-items: center;
            justify-content: center;
            margin-bottom: 0.45rem;
            animation: ifIconPulse 3.4s ease-in-out infinite;
            animation-delay: var(--card-delay);
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

        @keyframes ifTopbarBeam {
            0% { transform: translateX(-180%) rotate(18deg); }
            100% { transform: translateX(650%) rotate(18deg); }
        }

        @keyframes ifGemBob {
            0%, 100% { transform: translateY(0) rotate(0deg); }
            50% { transform: translateY(-3px) rotate(5deg); }
        }

        @keyframes ifGemGlow {
            0%, 100% { box-shadow: 0 8px 22px rgba(123, 47, 247, 0.35); }
            50% { box-shadow: 0 14px 30px rgba(67, 97, 238, 0.45); }
        }

        @keyframes ifGemSweep {
            0% { transform: translateX(-180%) skewX(-18deg); opacity: 0; }
            20% { opacity: 0.85; }
            65% { opacity: 0.85; }
            100% { transform: translateX(420%) skewX(-18deg); opacity: 0; }
        }

        @keyframes ifBrandShift {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }

        @keyframes ifSubPulse {
            0%, 100% { opacity: 0.75; }
            50% { opacity: 1; }
        }

        @keyframes ifStatusPulse {
            0%, 100% { box-shadow: 0 0 0 0 rgba(6, 214, 160, 0.18); }
            50% { box-shadow: 0 0 0 8px rgba(6, 214, 160, 0); }
        }

        @keyframes ifCapReveal {
            0% {
                opacity: 0;
                transform: translateY(14px) scale(0.98) rotateX(6deg);
            }
            100% {
                opacity: 1;
                transform: translateY(0) scale(1) rotateX(0deg);
            }
        }

        @keyframes ifCapFloat {
            0%, 100% { transform: translateY(0); }
            50% { transform: translateY(-4px); }
        }

        @keyframes ifCapShine {
            0% { transform: translateX(-200%) rotate(18deg); }
            45% { transform: translateX(420%) rotate(18deg); }
            100% { transform: translateX(420%) rotate(18deg); }
        }

        @keyframes ifIconPulse {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.08); }
        }

        @media (prefers-reduced-motion: reduce) {
            .if-topbar::before,
            .if-gem,
            .if-gem::after,
            .if-brand-title,
            .if-brand-sub,
            .if-status,
            .if-cap-head::after,
            .if-cap-card,
            .if-cap-card::before,
            .if-cap-icon {
                animation: none !important;
            }
        }

        .dash-panel {
            border: 1px solid var(--border2);
            border-radius: 18px;
            background: var(--glass);
            padding: 16px;
            margin: 0.2rem 0 1rem;
            backdrop-filter: blur(20px);
            box-shadow: var(--sh);
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

        .section-head {
            margin: 0.2rem 0 0.75rem;
            padding: 0.8rem 0.9rem;
            border-radius: 14px;
            border: 1px solid var(--border2);
            background: var(--glass);
            box-shadow: var(--sh);
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
            gap: 8px;
            border: 1px solid var(--border2);
            background: rgba(255, 255, 255, 0.92);
            border-radius: 13px;
            padding: 4px;
        }

        .stTabs [data-baseweb="tab"] {
            border-radius: 10px;
            color: var(--muted) !important;
            font-weight: 600;
            transition: all 0.2s ease;
            border: none;
            font-family: "Outfit", sans-serif !important;
        }

        .stTabs [aria-selected="true"] {
            background: linear-gradient(135deg, var(--blue), var(--indigo));
            color: #fff !important;
            box-shadow: 0 6px 18px rgba(67, 97, 238, 0.3);
        }

        .stButton > button {
            border-radius: 12px;
            border: none;
            font-weight: 700;
            letter-spacing: 0.01em;
            background: linear-gradient(135deg, var(--blue), var(--indigo), var(--violet));
            color: #fff;
            box-shadow: 0 8px 28px rgba(67, 97, 238, 0.28);
            transition: transform 0.15s ease, box-shadow 0.15s ease;
        }

        .stButton > button:hover {
            transform: translateY(-1px);
            box-shadow: 0 14px 34px rgba(67, 97, 238, 0.34);
        }

        .stTextInput input,
        .stTextArea textarea,
        div[data-baseweb="select"] > div,
        .stMultiSelect div[data-baseweb="select"] > div {
            background: #fff !important;
            border: 1px solid var(--border2) !important;
            border-radius: 11px !important;
            color: var(--text) !important;
        }

        div[data-testid="stFileUploader"] {
            border: 2px dashed rgba(67, 97, 238, 0.26);
            border-radius: 14px;
            padding: 10px;
            background: rgba(255, 255, 255, 0.72);
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
            background: linear-gradient(90deg, var(--blue), var(--indigo)) !important;
        }

        code, pre {
            border-radius: 8px !important;
            border: 1px solid var(--border) !important;
            background: #f8faff !important;
            color: var(--text) !important;
        }

        @media (max-width: 1024px) {
            .if-cap-grid {
                grid-template-columns: 1fr;
            }

            .dash-panel-grid {
                grid-template-columns: 1fr 1fr;
            }
        }

        @media (max-width: 780px) {
            .if-topbar {
                flex-direction: column;
                align-items: flex-start;
            }

            .if-badge-row {
                gap: 6px;
            }

            .dash-panel-grid {
                grid-template-columns: 1fr;
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
          <div class="if-grid-fog"></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar_brand():
    st.markdown(
        """
        <div class="space-brand">
          <div class="space-logo">
            <svg width="26" height="26" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
              <defs>
                <linearGradient id="logo_grad" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" stop-color="#37ddff"/>
                  <stop offset="100%" stop-color="#4386ff"/>
                </linearGradient>
              </defs>
              <polygon points="50,5 88,28 88,72 50,95 12,72 12,28" fill="none" stroke="url(#logo_grad)" stroke-width="6"/>
              <path d="M50 22 L73 78 L61 78 L56 66 L44 66 L39 78 L27 78 Z" fill="url(#logo_grad)"/>
              <rect x="43" y="50" width="14" height="7" fill="#071a31"/>
            </svg>
          </div>
          <div>
            <div class="space-brand-title">Invoice Intelligence AI</div>
            <div class="space-brand-sub">Invoice Workspace</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_main_header():
    st.markdown(
        """
        <div class="if-topbar">
          <div class="if-brand">
            <div class="if-gem">&#9889;</div>
            <div>
              <div class="if-brand-title">InvoiceFlow</div>
              <div class="if-brand-sub">workspace / upload-extract</div>
            </div>
          </div>
          <div class="if-status">ONLINE</div>
        </div>
        <div class="if-hero">
          <div class="if-hero-gem">AI</div>
          <div class="if-hero-title">InvoiceFlow</div>
          <div class="if-hero-sub">
            The intelligent invoice processing workspace. Upload, extract, review, and export structured data with production-grade reliability.
          </div>
          <div class="if-badge-row">
            <span class="if-badge">OCR Extraction</span>
            <span class="if-badge">Batch Processing</span>
            <span class="if-badge">Smart Review</span>
            <span class="if-badge">Instant Export</span>
            <span class="if-badge">Live Analytics</span>
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
            <div class="if-cap-sub">Everything InvoiceFlow does for you, visualized and production-ready.</div>
          </div>
        </div>
        <div class="if-cap-grid">
          <div class="if-cap-card">
            <div class="if-cap-icon">OCR</div>
            <div class="if-cap-name">AI OCR Extraction</div>
            <div class="if-cap-desc">Extracts vendor, dates, amounts, taxes, and line-items from scanned invoices.</div>
          </div>
          <div class="if-cap-card">
            <div class="if-cap-icon">UP</div>
            <div class="if-cap-name">Batch Upload</div>
            <div class="if-cap-desc">Upload many files or full zip folders and process them in one workflow.</div>
          </div>
          <div class="if-cap-card">
            <div class="if-cap-icon">REV</div>
            <div class="if-cap-name">Smart Review</div>
            <div class="if-cap-desc">Automatic review context with editable JSON and confidence visibility.</div>
          </div>
          <div class="if-cap-card">
            <div class="if-cap-icon">EXP</div>
            <div class="if-cap-name">Export Ready</div>
            <div class="if-cap-desc">Generate JSON, CSV, and Excel outputs directly from reviewed invoices.</div>
          </div>
          <div class="if-cap-card">
            <div class="if-cap-icon">OPS</div>
            <div class="if-cap-name">Live Status</div>
            <div class="if-cap-desc">Backend health, active invoice, and operational state are visible in real time.</div>
          </div>
          <div class="if-cap-card">
            <div class="if-cap-icon">SEC</div>
            <div class="if-cap-name">Secure Pipeline</div>
            <div class="if-cap-desc">Controlled upload/review/export flow with backend validation and traceability.</div>
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
        <div class="dash-metric">
          <div class="dash-label">Backend</div>
          <div class="dash-value">{backend_status}</div>
        </div>
        <div class="dash-metric">
          <div class="dash-label">Uploaded IDs</div>
          <div class="dash-value">{uploaded_count}</div>
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
      <div class="dash-label" style="margin-top:10px;">Live sync with backend endpoint and session state telemetry.</div>
    </div>
    """
    st.markdown(panel, unsafe_allow_html=True)


def render_section_intro(title: str, subtitle: str):
    st.markdown(
        f"""
        <div class="section-head">
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


def start_processing_for_upload(invoice_id: str, use_cache: bool) -> Dict[str, Any]:
    proc_res = post_json(
        f"{st.session_state.base_url}/process/start",
        {"invoice_id": invoice_id, "use_cache": use_cache},
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
        st.session_state.review_details = data
        st.session_state.review_json = json.dumps(data.get("extracted_data", {}), indent=2)
        st.session_state.review_loaded_invoice_id = invoice_id
        st.session_state.review_load_error = None
        return True, None

    detail = data.get("detail") if isinstance(data, dict) else data
    message = str(detail)
    st.session_state.review_details = None
    st.session_state.review_json = ""
    st.session_state.review_loaded_invoice_id = invoice_id
    st.session_state.review_load_error = message
    return False, message


def upload_invoice_entries(
    entries: List[Tuple[str, bytes, str]],
    auto_process: bool,
    use_cache: bool,
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
                processing = start_processing_for_upload(invoice_id, use_cache)

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

    st.dataframe(rows, use_container_width=True)
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
        when = relative_time_text(item.get("uploaded_at"))
        rows.append(
            f"""
            <div class="if-recent-item">
              <div class="if-recent-name">{file_name}</div>
              <div class="if-recent-meta">{when} · {invoice_id}</div>
              <span class="if-recent-state">{status}</span>
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
        <div class="if-recent-shell">
          <div class="if-recent-head">
            <div class="if-recent-title">Recent Files</div>
            <div class="if-recent-sub">Latest processed invoices in this session</div>
          </div>
          <div class="if-recent-body">
            <div class="if-recent-grid">
              <div class="if-mini">
                <div class="if-mini-val">{completed}</div>
                <div class="if-mini-lbl">DONE</div>
              </div>
              <div class="if-mini">
                <div class="if-mini-val">{running}</div>
                <div class="if-mini-lbl">RUNNING</div>
              </div>
              <div class="if-mini">
                <div class="if-mini-val">{failed}</div>
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
    if "base_url" not in st.session_state:
        st.session_state.base_url = "http://localhost:8000/api"
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


def api_headers() -> dict:
    return {}

def root_url(base_url: str) -> str:
    return base_url[:-4] if base_url.endswith("/api") else base_url

def check_backend(base_url: str, timeout: float = 10.0) -> Tuple[bool, str]:
    try:
        res = requests.get(f"{root_url(base_url)}/health", timeout=timeout)
        if res.status_code == 200:
            return True, "healthy"
        return False, f"status {res.status_code}"
    except RequestException as e:
        return False, str(e)

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
            "8000",
        ]
        proc = subprocess.Popen(cmd, cwd=".")
        st.session_state.backend_proc = proc
        st.session_state.backend_started_at = time.time()
        return True, "Backend process started."
    except Exception as e:
        return False, f"Failed to start backend: {e}"

def auto_start_backend():
    if st.session_state.backend_autostart_attempted:
        return
    st.session_state.backend_autostart_attempted = True
    ok, _ = start_backend_process()
    if not ok:
        return
    # Wait briefly for the server to come up
    for _ in range(30):
        time.sleep(1.0)
        ok, status = check_backend(st.session_state.base_url, timeout=3.0)
        if ok:
            st.session_state.backend_ok = True
            st.session_state.backend_status = status
            return


def post_json(url: str, payload: Optional[dict] = None, use_auth: bool = True, timeout: float = 15.0):
    headers = {}
    if use_auth:
        headers.update(api_headers())
    try:
        if payload is None:
            return requests.post(url, headers=headers, timeout=timeout)
        headers["Content-Type"] = "application/json"
        return requests.post(url, json=payload, headers=headers, timeout=timeout)
    except RequestException as e:
        return {"_error": f"Backend offline. Start it on port 8000. Details: {e}"}


def get_json(url: str, timeout: float = 15.0):
    try:
        return requests.get(url, headers=api_headers(), timeout=timeout)
    except RequestException as e:
        return {"_error": f"Backend offline. Start it on port 8000. Details: {e}"}


def upload_single_file(base_url: str, filename: str, content: bytes, content_type: str):
    files = {"files": (filename, content, content_type)}
    try:
        return requests.post(f"{base_url}/invoices/upload", headers=api_headers(), files=files, timeout=60)
    except RequestException as e:
        return {"_error": str(e)}


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
        <div class="if-upload-shell">
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

        if mode == "Batch files":
            files = st.file_uploader(
                "Select invoice files",
                type=["pdf", "png", "jpg", "jpeg", "tif", "tiff"],
                accept_multiple_files=True,
                key="upload_batch_files",
            )
            clicked = st.button("Upload Selected Files", use_container_width=True, type="primary", key="upload_batch_button")
            if clicked:
                if not files:
                    st.warning("Please select at least one file.")
                else:
                    entries = [(f.name, f.getvalue(), f.type or "application/octet-stream") for f in files]
                    results = upload_invoice_entries(entries, auto_process=auto_process, use_cache=use_cache)
        else:
            zip_file = st.file_uploader(
                "Upload a zip file containing invoices",
                type=["zip"],
                key="upload_zip_file",
            )
            clicked = st.button("Upload Zip Contents", use_container_width=True, type="primary", key="upload_zip_button")
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
                        results = upload_invoice_entries(extracted, auto_process=auto_process, use_cache=use_cache)

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

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Start Processing", use_container_width=True, type="primary", key="start_processing_btn"):
            if not invoice_id:
                st.warning("Please enter an invoice ID.")
                return
            payload = {"invoice_id": invoice_id, "use_cache": use_cache}
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
        if st.button("Check Status", use_container_width=True, key="check_processing_btn"):
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
        if st.button("Clear Status", use_container_width=True, key="clear_processing_btn"):
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
    if (
        st.session_state.get("review_loaded_invoice_id") != invoice_id
        or st.session_state.get("review_details") is None
    ):
        load_review_details_for_invoice(invoice_id)

    with action_col1:
        if st.button("Refresh Details", use_container_width=True, type="primary", key="refresh_review_btn"):
            load_review_details_for_invoice(invoice_id)
    with action_col2:
        if st.button("Clear Review", use_container_width=True, key="clear_review_btn"):
            st.session_state.review_details = None
            st.session_state.review_json = ""
            st.session_state.review_loaded_invoice_id = None
            st.session_state.review_load_error = None

    details = st.session_state.review_details
    if not details:
        st.info(f"Review data for invoice {invoice_id} is not ready yet.")
        last_error = st.session_state.get("review_load_error")
        if last_error:
            st.caption(f"Latest status: {last_error}")
        st.caption("Processing starts automatically in Upload. Click Refresh Details after a few seconds.")
        return

    if not isinstance(details, dict):
        st.error("Unexpected review details format.")
        return

    if details.get("invoice_id") != invoice_id:
        st.info("Loaded details were stale. Refreshing for selected invoice.")
        load_review_details_for_invoice(invoice_id)
        return

    extracted_data = details.get("extracted_data", {})
    confidence_scores = details.get("confidence_scores", {})
    meta_col1, meta_col2, meta_col3 = st.columns(3)
    meta_col1.metric("Filename", details.get("filename") or "-")
    meta_col2.metric("Processing Status", details.get("processing_status") or "-")
    meta_col3.metric("Extracted Fields", len(extracted_data))

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
        st.dataframe(confidence_rows, use_container_width=True)

    edited_json = st.text_area(
        "Extracted Data (JSON)",
        key="review_json",
        height=320,
        help="Edit values directly in JSON format before submitting.",
    )
    notes = st.text_area("Review Notes", key="review_notes", placeholder="Optional reviewer notes")
    approved = st.checkbox("Approve invoice", value=True, key="review_approved")

    if st.button("Submit Review", use_container_width=True, type="primary", key="submit_review_btn"):
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

    if st.button("Generate Export", use_container_width=True, type="primary", key="export_btn"):
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
    if st.button("Refresh History", use_container_width=True, type="primary", key="refresh_history_btn"):
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
    st.dataframe(filtered_rows, use_container_width=True)


def main():
    st.set_page_config(page_title="Invoice Processing", layout="wide", initial_sidebar_state="collapsed")
    init_state()
    apply_futuristic_theme()
    render_live_background()
    render_main_header()
    render_capability_cards()

    backend_ok, backend_status = check_backend(st.session_state.base_url)
    st.session_state.backend_ok = backend_ok
    st.session_state.backend_status = backend_status
    if not backend_ok:
        auto_start_backend()
        backend_ok, backend_status = check_backend(st.session_state.base_url)
        st.session_state.backend_ok = backend_ok
        st.session_state.backend_status = backend_status

    render_dashboard_panel(st.session_state.backend_ok, st.session_state.backend_status)

    if not st.session_state.get("backend_ok", False):
        st.error("Backend is offline. Start it on port 8000 and try again.")
        st.caption("Run: uvicorn backend.app.main:app --reload --port 8000")
        st.caption(f"Details: {st.session_state.get('backend_status')}")
        return

    tabs = st.tabs(["Upload", "Review", "Export"])
    with tabs[0]:
        render_upload()
    with tabs[1]:
        render_review()
    with tabs[2]:
        render_export()


if __name__ == "__main__":
    main()

