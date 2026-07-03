import type { LayoutConfig } from './layout';
import { DEFAULT_CONFIG } from './layout';

/** 导出 Canvas 内容为 PNG */
export function exportToPNG(
  canvas: HTMLCanvasElement,
  scale: number = 2,
): Promise<Blob> {
  const offscreen = document.createElement('canvas');
  offscreen.width = canvas.width * scale / (window.devicePixelRatio || 1);
  offscreen.height = canvas.height * scale / (window.devicePixelRatio || 1);
  const offCtx = offscreen.getContext('2d')!;
  offCtx.scale(scale, scale);
  offCtx.drawImage(canvas, 0, 0, canvas.width / (window.devicePixelRatio || 1), canvas.height / (window.devicePixelRatio || 1));

  return new Promise((resolve, reject) => {
    offscreen.toBlob(blob => {
      if (blob) resolve(blob);
      else reject(new Error('Failed to export PNG'));
    }, 'image/png');
  });
}

/** 下载 PNG 文件 */
export async function downloadPNG(
  canvas: HTMLCanvasElement,
  filename: string = 'jianpu-score.png',
  scale: number = 2,
) {
  const blob = await exportToPNG(canvas, scale);
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

/** 计算渲染所需尺寸 */
export function getCanvasSize(
  layoutHeight: number,
  config: LayoutConfig = DEFAULT_CONFIG,
) {
  const dpr = window.devicePixelRatio || 1;
  return {
    width: config.canvasWidth * dpr,
    height: layoutHeight * dpr,
    cssWidth: config.canvasWidth,
    cssHeight: layoutHeight,
    dpr,
  };
}

/** 设置 Canvas DPI 适配 */
export function setupCanvasDPI(
  canvas: HTMLCanvasElement,
  cssWidth: number,
  cssHeight: number,
): CanvasRenderingContext2D {
  const dpr = window.devicePixelRatio || 1;
  canvas.width = cssWidth * dpr;
  canvas.height = cssHeight * dpr;
  canvas.style.width = `${cssWidth}px`;
  canvas.style.height = `${cssHeight}px`;
  const ctx = canvas.getContext('2d')!;
  ctx.scale(dpr, dpr);
  return ctx;
}
