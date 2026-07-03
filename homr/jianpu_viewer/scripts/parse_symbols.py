#!/usr/bin/env python3
"""Parse all symbol_*.txt SVG files and generate TypeScript symbol entries - clean output."""

import os
import xml.etree.ElementTree as ET

ICONS_DIR = "/vol1/1000/projects/jianpu-renderer/res/fanqie_jianpu_icons"

def parse_svg(filepath):
    """Parse a symbol SVG file, extract path data and viewport info."""
    with open(filepath, 'r') as f:
        content = f.read()
    
    root = ET.fromstring(content)
    
    # Find the mask rect for viewport
    mask_rect = None
    for rect in root.iter('{http://www.w3.org/2000/svg}rect'):
        if rect.get('mask') == 'true' or rect.get('fill') == '#ffff00':
            mask_rect = rect
            break
    
    if mask_rect is None:
        for rect in root.iter('rect'):
            if rect.get('mask') == 'true' or rect.get('fill') == '#ffff00':
                mask_rect = rect
                break
    
    vw = float(mask_rect.get('width', '0'))
    vh = float(mask_rect.get('height', '0'))
    x = float(mask_rect.get('x', '0'))
    y = float(mask_rect.get('y', '0'))
    
    cx = -x
    cy = -y
    
    # Collect all drawing elements (non-mask)
    paths = []
    has_stroke = False
    has_fill = False
    
    for elem in root.iter():
        tag = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
        
        if tag == 'rect' and elem.get('mask') != 'true' and elem.get('fill') != '#ffff00':
            rx = float(elem.get('x', '0'))
            ry = float(elem.get('y', '0'))
            rw = float(elem.get('width', '0'))
            rh = float(elem.get('height', '0'))
            path_str = f"M{rx},{ry}h{rw}v{rh}h{-rw}Z"
            paths.append(path_str)
            fill = elem.get('fill')
            stroke = elem.get('stroke')
            if fill and fill != 'none':
                has_fill = True
            if stroke and stroke != 'none':
                has_stroke = True
        
        elif tag == 'ellipse':
            ex = float(elem.get('cx', '0'))
            ey = float(elem.get('cy', '0'))
            erx = float(elem.get('rx', '0'))
            ery = float(elem.get('ry', '0'))
            c = 0.5522847498
            path_str = f"M{ex - erx},{ey}C{ex - erx},{ey - ery * c} {ex - erx * c},{ey - ery} {ex},{ey - ery}C{ex + erx * c},{ey - ery} {ex + erx},{ey - ery * c} {ex + erx},{ey}C{ex + erx},{ey + ery * c} {ex + erx * c},{ey + ery} {ex},{ey + ery}C{ex - erx * c},{ey + ery} {ex - erx},{ey + ery * c} {ex - erx},{ey}Z"
            paths.append(path_str)
            fill = elem.get('fill')
            stroke = elem.get('stroke')
            if fill and fill != 'none':
                has_fill = True
            if stroke and stroke != 'none':
                has_stroke = True
        
        elif tag == 'path':
            d = elem.get('d', '').strip()
            if d:
                paths.append(d)
                stroke = elem.get('stroke')
                fill = elem.get('fill')
                if stroke and stroke != 'none':
                    has_stroke = True
                if fill and fill != 'none':
                    has_fill = True
        
        elif tag == 'line':
            x1 = float(elem.get('x1', '0'))
            y1 = float(elem.get('y1', '0'))
            x2 = float(elem.get('x2', '0'))
            y2 = float(elem.get('y2', '0'))
            path_str = f"M{x1},{y1}L{x2},{y2}"
            paths.append(path_str)
            stroke = elem.get('stroke')
            if stroke and stroke != 'none':
                has_stroke = True
    
    combined_path = ' '.join(paths)
    is_stroke = has_stroke and not has_fill
    
    return {
        'path': combined_path,
        'vw': vw,
        'vh': vh,
        'cx': cx,
        'cy': cy,
        'stroke': is_stroke,
    }

def fmt(n):
    if isinstance(n, float):
        if n == int(n):
            return str(int(n))
        s = f"{n:.4f}"
        s = s.rstrip('0').rstrip('.')
        return s
    return str(n)

def main():
    existing = {1, 2, 3, 8, 10, 11, 12, 13, 14, 17, 18, 19, 20, 43, 45, 100, 101}
    
    for i in range(1, 53):
        if i in existing:
            continue
        
        filepath = os.path.join(ICONS_DIR, f"symbol_{i}.txt")
        if not os.path.exists(filepath):
            continue
        
        try:
            d = parse_svg(filepath)
            stroke_opt = "stroke: true, " if d['stroke'] else ""
            path = d['path']
            print(f"  {i}: {{")
            print(f"    path: \"{path}\",")
            print(f"    vw: {fmt(d['vw'])}, vh: {fmt(d['vh'])}, cx: {fmt(d['cx'])}, cy: {fmt(d['cy'])}, {stroke_opt}")
            print(f"  }},")
        except Exception as e:
            print(f"// ERROR symbol_{i}: {e}")

if __name__ == '__main__':
    main()
