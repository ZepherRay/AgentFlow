<template>
  <router-view />
</template>

<style>
/* ═══════════════════════════════════════════════
   Global Design System — Dark Glassmorphism Theme
   ═══════════════════════════════════════════════ */
:root {
  /* Base backgrounds */
  --bg-0: #0c1328;
  --bg-1: #121a30;
  --bg-2: #182240;
  --bg-3: #1f2c50;
  --surface: rgba(255,255,255,0.06);
  --surface-2: rgba(255,255,255,0.10);
  --surface-3: rgba(255,255,255,0.14);

  /* Borders */
  --border: rgba(255,255,255,0.10);
  --border-2: rgba(255,255,255,0.16);
  --border-3: rgba(255,255,255,0.24);

  /* Text */
  --t-0: #f8fafc;
  --t-1: #e2e8f0;
  --t-2: #cbd5e1;
  --t-3: #94a3b8;
  --t-4: #64748b;

  /* Accent — Indigo/Violet */
  --ac: #6366f1;
  --ac-2: #818cf8;
  --ac-3: #a78bfa;
  --ac-glow: rgba(99,102,241,0.4);
  --ac-grad: linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #a855f7 100%);

  /* Semantic */
  --emerald: #10b981;
  --emerald-glow: rgba(16,185,129,0.3);
  --amber: #f59e0b;
  --amber-glow: rgba(245,158,11,0.3);
  --rose: #f43f5e;
  --rose-glow: rgba(244,63,94,0.3);
  --cyan: #06b6d4;
  --cyan-glow: rgba(6,182,212,0.3);

  /* Radius */
  --r-sm: 8px;
  --r-md: 12px;
  --r-lg: 16px;
  --r-xl: 20px;
  --r-2xl: 24px;

  /* Shadows */
  --sh-sm: 0 2px 8px rgba(0,0,0,0.2);
  --sh-md: 0 8px 24px rgba(0,0,0,0.3);
  --sh-lg: 0 16px 48px rgba(0,0,0,0.4);
  --sh-glow: 0 0 32px var(--ac-glow);
}

* { margin: 0; padding: 0; box-sizing: border-box; }
html, body, #app { height: 100%; overflow: hidden; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, 'PingFang SC', 'Microsoft YaHei', sans-serif; }

body {
  background: var(--bg-0);
  color: var(--t-0);
  font-size: 14px;
  line-height: 1.5;
  -webkit-font-smoothing: antialiased;
}

/* Animated gradient mesh background */
body::before {
  content: '';
  position: fixed;
  inset: 0;
  background:
    radial-gradient(ellipse 60% 50% at 15% 10%, rgba(99,102,241,0.12) 0%, transparent 60%),
    radial-gradient(ellipse 50% 40% at 85% 90%, rgba(168,85,247,0.08) 0%, transparent 60%),
    radial-gradient(ellipse 40% 30% at 70% 15%, rgba(6,182,212,0.06) 0%, transparent 60%),
    var(--bg-0);
  z-index: 0;
  animation: meshShift 20s ease-in-out infinite alternate;
  pointer-events: none;
}
@keyframes meshShift {
  0% { transform: scale(1) translate(0,0); }
  100% { transform: scale(1.05) translate(-1%, -1%); }
}

/* Scrollbar */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: rgba(255,255,255,0.2); }

/* Element Plus dark-theme variable overrides */
:root {
  --el-bg-color: var(--bg-1);
  --el-bg-color-overlay: var(--bg-2);
  --el-text-color-primary: var(--t-0);
  --el-text-color-regular: var(--t-1);
  --el-text-color-secondary: var(--t-2);
  --el-text-color-placeholder: var(--t-3);
  --el-border-color: var(--border-2);
  --el-border-color-light: var(--border);
  --el-border-color-lighter: var(--border);
  --el-border-color-extra-light: var(--border);
  --el-fill-color: var(--bg-2);
  --el-fill-color-light: var(--bg-3);
  --el-fill-color-lighter: var(--surface-3);
  --el-fill-color-blank: var(--bg-2);
  --el-mask-color: rgba(7,11,22,0.7);
  --el-mask-color-extra-light: rgba(7,11,22,0.4);
  --el-color-white: var(--bg-1);
  --el-color-black: var(--t-0);
  --el-color-primary: var(--ac);
  --el-color-primary-light-3: var(--ac-2);
  --el-color-primary-light-5: var(--ac-3);
  --el-color-primary-light-7: rgba(99,102,241,0.3);
  --el-color-primary-dark-2: #4f46e5;
  --el-color-success: var(--emerald);
  --el-color-warning: var(--amber);
  --el-color-danger: var(--rose);
  --el-color-info: var(--t-3);
  --el-color-error: var(--rose);
  --el-border-radius-base: var(--r-sm);
  --el-border-radius-small: 6px;
  --el-border-radius-round: 20px;
  --el-box-shadow: var(--sh-md);
  --el-box-shadow-light: var(--sh-sm);
  --el-box-shadow-lighter: var(--sh-sm);
  --el-box-shadow-dark: var(--sh-lg);
  --el-font-size-base: 14px;
  --el-font-size-small: 12px;
  --el-font-size-large: 16px;
  --el-font-weight-primary: 500;
}

/* Element Plus component overrides */
.el-select-dropdown,
.el-dropdown-menu,
.el-picker-panel,
.el-date-picker,
.el-time-panel {
  background: var(--bg-2) !important;
  border: 1px solid var(--border-2) !important;
}
.el-select-dropdown__item.hover,
.el-select-dropdown__item:hover,
.el-dropdown-menu__item:hover {
  background: var(--surface-3) !important;
}
.el-select-dropdown__item.selected {
  color: var(--ac-2) !important;
  font-weight: 600;
}
.el-input__wrapper,
.el-select__wrapper {
  background: var(--bg-2) !important;
  border: 1px solid var(--border) !important;
  box-shadow: none !important;
}
.el-input__wrapper:hover,
.el-select__wrapper:hover {
  border-color: var(--border-2) !important;
}
.el-input__wrapper.is-focus,
.el-select__wrapper.is-focused {
  border-color: var(--ac) !important;
  box-shadow: 0 0 0 3px var(--ac-glow) !important;
}
.el-input__inner,
.el-select__input {
  color: var(--t-0) !important;
  caret-color: var(--ac);
}
.el-input__inner::placeholder,
.el-select__input::placeholder {
  color: var(--t-3) !important;
}
.el-button--primary {
  --el-button-bg-color: var(--ac) !important;
  --el-button-border-color: var(--ac) !important;
  --el-button-hover-bg-color: var(--ac-2) !important;
  --el-button-hover-border-color: var(--ac-2) !important;
  --el-button-active-bg-color: #4f46e5 !important;
  --el-button-active-border-color: #4f46e5 !important;
}
.el-button--default {
  --el-button-bg-color: var(--surface) !important;
  --el-button-border-color: var(--border) !important;
  --el-button-text-color: var(--t-1) !important;
  --el-button-hover-bg-color: var(--surface-2) !important;
  --el-button-hover-border-color: var(--border-2) !important;
  --el-button-hover-text-color: var(--t-0) !important;
  --el-button-active-bg-color: var(--surface-3) !important;
  --el-button-active-border-color: var(--border-3) !important;
}
.el-dialog {
  --el-dialog-bg-color: var(--bg-1) !important;
  --el-dialog-border-color: var(--border-2) !important;
  --el-dialog-title-font-size: 17px;
  --el-dialog-content-font-size: 14px;
  --el-dialog-padding-primary: 24px;
}
.el-dialog__header {
  border-bottom: 1px solid var(--border);
  padding: 20px 24px 16px;
  margin-right: 0 !important;
}
.el-dialog__title {
  color: var(--t-0) !important;
  font-weight: 600;
}
.el-dialog__body {
  padding: 24px !important;
}
.el-dialog__footer {
  border-top: 1px solid var(--border);
  padding: 16px 24px;
}
.el-overlay-dialog {
  background: rgba(7,11,22,0.7);
  backdrop-filter: blur(8px);
}
.el-message-box {
  background: var(--bg-1) !important;
  border: 1px solid var(--border-2) !important;
}
.el-message-box__title {
  color: var(--t-0) !important;
}
.el-message-box__message {
  color: var(--t-2) !important;
}
.el-tag {
  --el-tag-bg-color: var(--surface-2) !important;
  --el-tag-border-color: var(--border) !important;
  --el-tag-text-color: var(--t-1) !important;
}
.el-tag.el-tag--primary {
  --el-tag-bg-color: var(--ac-glow) !important;
  --el-tag-border-color: transparent !important;
  --el-tag-text-color: var(--ac-2) !important;
}
.el-tag.el-tag--success {
  --el-tag-bg-color: rgba(16,185,129,0.12) !important;
  --el-tag-text-color: var(--emerald) !important;
}
.el-tag.el-tag--warning {
  --el-tag-bg-color: rgba(245,158,11,0.12) !important;
  --el-tag-text-color: var(--amber) !important;
}
.el-tag.el-tag--danger {
  --el-tag-bg-color: rgba(244,63,94,0.12) !important;
  --el-tag-text-color: var(--rose) !important;
}
.el-table {
  --el-table-bg-color: transparent !important;
  --el-table-tr-bg-color: transparent !important;
  --el-table-header-bg-color: transparent !important;
  --el-table-border-color: var(--border) !important;
  --el-table-text-color: var(--t-1) !important;
  --el-table-header-text-color: var(--t-3) !important;
  --el-table-row-hover-bg-color: var(--surface-2) !important;
}
.el-table th.el-table__cell {
  border-bottom: 1px solid var(--border) !important;
}
.el-table td.el-table__cell {
  border-bottom: 1px solid var(--border) !important;
}
.el-collapse {
  --el-collapse-header-bg-color: transparent !important;
  --el-collapse-content-bg-color: transparent !important;
  --el-collapse-border-color: var(--border) !important;
  --el-collapse-header-text-color: var(--t-1) !important;
  --el-collapse-content-text-color: var(--t-2) !important;
}
.el-collapse-item__header {
  color: var(--t-1) !important;
}
.el-collapse-item__wrap {
  background: transparent !important;
}
.el-slider__runway {
  background: var(--surface-3) !important;
}
.el-slider__bar {
  background: var(--ac-grad) !important;
}
.el-slider__button {
  border-color: var(--ac) !important;
}
.el-select__popper,
.el-dropdown__popper {
  background: var(--bg-2) !important;
  border: 1px solid var(--border-2) !important;
}
.el-popper {
  background: var(--bg-2) !important;
  border: 1px solid var(--border-2) !important;
}
.el-popper .el-popper__arrow::before {
  background: var(--bg-2) !important;
  border-color: var(--border-2) !important;
}
.el-notification {
  background: var(--bg-2) !important;
  border: 1px solid var(--border-2) !important;
}
.el-message {
  background: var(--bg-2) !important;
  border: 1px solid var(--border-2) !important;
}
.el-divider {
  --el-divider-border-color: var(--border) !important;
}
.el-upload-dragger {
  background: var(--bg-2) !important;
  border: 2px dashed var(--border-2) !important;
  border-radius: var(--r-lg) !important;
}
.el-upload-dragger:hover {
  border-color: var(--ac) !important;
}
.el-upload__tip {
  color: var(--t-3) !important;
}
.el-progress-bar__outer {
  background: var(--surface-3) !important;
}
.el-progress-bar__inner {
  background: var(--ac-grad) !important;
}
.el-empty__description p {
  color: var(--t-3) !important;
}
.el-switch__core {
  background: var(--surface-3) !important;
  border-color: var(--border) !important;
}
.el-switch.is-checked .el-switch__core {
  background: var(--ac) !important;
  border-color: var(--ac) !important;
}
</style>
