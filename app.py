import os
import random
from datetime import datetime
from PIL import Image
import pandas as pd
import streamlit as st

# 嘗試引入翻譯套件
try:
  from deep_translator import GoogleTranslator

  HAS_TRANSLATOR = True
except ImportError:
  HAS_TRANSLATOR = False

# --- 設定路徑與檔案 ---
EXCEL_FILE = 'data.xlsx'
IMAGE_FOLDER = 'images'

st.set_page_config(
    page_title='My Closet Stylist Edition', page_icon='✨', layout='wide'
)

# ==========================================
# ★★★ CSS 時尚美化區 ★★★
# ==========================================
st.markdown(
    """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Lato:wght@300;400;700&family=Playfair+Display:wght@700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Lato', sans-serif;
        color: #333;
    }
    
    h1, h2, h3 {
        font-family: 'Playfair Display', serif !important;
        font-weight: 700 !important;
        letter-spacing: 0.5px;
    }
    
    div[data-testid="stImage"] {
        background-color: white;
        padding: 10px;
        border-radius: 12px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
        border: 1px solid #f5f5f5;
    }
    div[data-testid="stImage"]:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 25px rgba(0,0,0,0.1);
    }
    div[data-testid="stImage"] img {
        height: 340px !important;
        object-fit: contain !important;
        margin: 0 auto !important;
    }

    div.stButton > button {
        background-color: #1E1E1E !important;
        color: white !important;
        border-radius: 30px !important;
        border: none !important;
        padding: 10px 15px !important;
        font-weight: 500 !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        transition: all 0.3s ease !important;
    }
    div.stButton > button:hover {
        transform: scale(1.02);
        background-color: #444 !important;
        box-shadow: 0 6px 12px rgba(0,0,0,0.15);
    }
    
    div[data-testid="column"] {
        display: flex !important;
        flex-direction: column !important;
        align-items: center !important; 
        text-align: center !important;
    }
    .stCaption {
        font-size: 13px !important;
        color: #777 !important;
        margin-top: 3px !important;
    }
    div[data-testid="stCheckbox"] {
        margin-top: 5px;
        padding: 3px 12px;
        background: #f8f9fa;
        border-radius: 15px;
    }
</style>
""",
    unsafe_allow_html=True,
)


# --- 1. 讀取資料庫 ---
@st.cache_data
def load_data():
  try:
    df = pd.read_excel(EXCEL_FILE, dtype={'ID': str})
    df.columns = df.columns.str.strip()

    cols_to_str = [
        'Category',
        'Fit',
        'ColorGroup',
        'Season',
        'Style',
        'Color',
        'Aesthetic',
    ]
    for col in cols_to_str:
      if col in df.columns:
        df[col] = df[col].astype(str)

    if 'Thickness' in df.columns:
      df['Thickness'] = pd.to_numeric(df['Thickness'], errors='coerce')
    if 'Noise' not in df.columns:
      df['Noise'] = 1
    else:
      df['Noise'] = pd.to_numeric(df['Noise'], errors='coerce').fillna(1)

    return df
  except Exception:
    return pd.DataFrame()


df = load_data()


# --- 2. 輔助功能 ---
def create_placeholder_image(text='No Item'):
  img = Image.new('RGB', (350, 350), color='#f4f4f4')
  return img


def find_image_path(image_id):
  if not image_id or not os.path.exists(IMAGE_FOLDER):
    return None
  valid_exts = ['.jpg', '.jpeg', '.png', '.JPG', '.PNG', '.heic', '.HEIC']
  valid_separators = ['.', '_', '-', ' ']
  candidates = []
  try:
    for filename in os.listdir(IMAGE_FOLDER):
      if filename.startswith(image_id):
        remaining = filename[len(image_id) :]
        if len(remaining) == 0 or remaining[0] in valid_separators:
          if any(filename.endswith(ext) for ext in valid_exts):
            candidates.append(filename)
    if not candidates:
      return None
    candidates.sort()
    return os.path.join(IMAGE_FOLDER, candidates[0])
  except Exception:
    return None


@st.cache_data
def translate_to_jp(text):
  if not text or not HAS_TRANSLATOR:
    return text
  try:
    return GoogleTranslator(source='zh-TW', target='ja').translate(text)
  except:
    return text


def get_current_season():
  m = datetime.now().month
  if m in [3, 4, 5]:
    return '春'
  elif m in [6, 7, 8]:
    return '夏'
  elif m in [9, 10, 11]:
    return '秋'
  else:
    return '冬'


# --- 3. 強約束核心搭配演算法 (防硬塞夏季外套) ---
def auto_generate_advanced(preset_style=None, season=None):
  if df.empty:
    return

  slots_keywords = {
      'id_pant': '下|Bot|Pant|褲|裙|Legging',
      'id_shoes': '鞋|Shoe|Boot|Sneaker',
      'id_top': '上|Top|Shirt|T恤|衫',
      'id_outer': '外|Coat|Jacket|Outer',
  }

  def filter_by_style(pool, style_name, category_key):
    if pool.empty:
      return pool

    if style_name == 'CityBoy':
      if category_key == 'id_pant':
        m = pool[
            pool['Fit'].isin(['Loose', 'Wide'])
            | pool['Aesthetic'].str.contains('City Boy', case=False, na=False)
        ]
        return m if not m.empty else pool
      elif category_key in ['id_top', 'id_outer']:
        m = pool[
            (
                pool['Fit'].isin(['Loose', 'Oversized'])
                | pool['Aesthetic'].str.contains(
                    'City Boy', case=False, na=False
                )
            )
            & (pool['Noise'] <= 2)
        ]
        return m if not m.empty else pool
      elif category_key == 'id_shoes':
        m = pool[
            pool['Name'].str.contains(
                '990|992|Salomon|wallabee|KAYANO|Presto|XA|Force|Dunk',
                case=False,
                na=False,
            )
            | pool['Aesthetic'].str.contains('City Boy', case=False, na=False)
        ]
        return m if not m.empty else pool

    elif style_name == 'Minimal':
      if category_key in ['id_pant', 'id_top', 'id_outer']:
        m = pool[
            (pool['Noise'] <= 1)
            & pool['Aesthetic'].str.contains(
                'Minimal|Smart', case=False, na=False
            )
        ]
        return (
            m
            if not m.empty
            else pool[pool['Aesthetic'].str.contains('Minimal', na=False)]
        )
      elif category_key == 'id_shoes':
        m = pool[
            pool['Name'].str.contains(
                '皮鞋|靴|Force|Dunk|Loafer|Moc', case=False, na=False
            )
            | pool['Aesthetic'].str.contains('Minimal', na=False)
        ]
        return m if not m.empty else pool

    elif style_name == 'Workwear':
      if category_key in ['id_pant', 'id_top', 'id_outer']:
        m = pool[
            pool['Style'].str.contains('美式|軍事|工裝', case=False, na=False)
            | pool['Brand'].str.contains(
                'Garments|Carhartt|Dickies|Barbour|WAIPER|KM|MINEDENIM',
                case=False,
                na=False,
            )
            | pool['Aesthetic'].str.contains(
                'Workwear|Military', case=False, na=False
            )
            | (
                pool['Aesthetic'].str.contains('Vintage', case=False, na=False)
                & ~pool['Aesthetic'].str.contains('Minimal', na=False)
            )
        ]
        return m if not m.empty else pool
      elif category_key == 'id_shoes':
        m = pool[
            pool['Name'].str.contains(
                '靴|DANNER|TIMBERLAND|wallabee', case=False, na=False
            )
            | pool['Aesthetic'].str.contains('Workwear', case=False, na=False)
        ]
        return m if not m.empty else pool

    elif style_name == 'Grunge':
      if category_key in ['id_pant', 'id_top', 'id_outer']:
        m = pool[
            (
                pool['Brand'].str.contains(
                    'UNDERCOVER|Supreme|SWAGGER|number'
                    ' nine|APE|Palace|FAT|underpeace',
                    case=False,
                    na=False,
                )
                | pool['Aesthetic'].str.contains(
                    'Grunge|Punk|Skater', case=False, na=False
                )
                | (
                    pool['Style'].str.contains('潮流', case=False, na=False)
                    & (pool['Noise'] >= 2)
                )
            )
            & (
                ~pool['Aesthetic'].str.contains(
                    'Minimalist|Minimal', case=False, na=False
                )
            )
        ]
        return m if not m.empty else pool
      elif category_key == 'id_shoes':
        m = pool[
            pool['Name'].str.contains(
                'Air Max|VaporMax|微笑鞋|皮鞋|靴|TERMINATOR',
                case=False,
                na=False,
            )
            | pool['Brand'].str.contains('UNDERCOVER', case=False, na=False)
        ]
        return m if not m.empty else pool

    return pool

  # 1. 褲裝優先 (Bottom First)
  current_pant_id = st.session_state.get('id_pant', '')
  pant_noise = 1
  pant_color_group = None

  if not st.session_state.get('lock_id_pant', False):
    pool_pant = df[
        df['Category'].str.contains(
            slots_keywords['id_pant'], case=False, na=False
        )
    ].copy()

    if season and 'Season' in pool_pant.columns:
      pool_pant = pool_pant[
          pool_pant['Season'].str.contains(
              f'{season}|四季|All', case=False, na=False
          )
      ]

    if preset_style:
      pool_pant = filter_by_style(pool_pant, preset_style, 'id_pant')

    if not pool_pant.empty:
      picked_pant = pool_pant.sample(1).iloc[0]
      current_pant_id = str(picked_pant['ID'])
      st.session_state['id_pant'] = current_pant_id
      pant_noise = int(picked_pant.get('Noise', 1))
      pant_color_group = str(picked_pant.get('ColorGroup', ''))
  else:
    pant_row = df[df['ID'] == current_pant_id]
    if not pant_row.empty:
      pant_noise = int(pant_row.iloc[0].get('Noise', 1))
      pant_color_group = str(pant_row.iloc[0].get('ColorGroup', ''))

  # 2. 聯動搭配 鞋款 ➔ 上衣 ➔ 外套
  process_order = ['id_shoes', 'id_top', 'id_outer']

  for key in process_order:
    if st.session_state.get(f'lock_{key}', False):
      continue

    # ★★★ 夏季防硬塞外套保護機制 ★★★
    if key == 'id_outer' and season == '夏':
      pool_summer_outer = df[
          df['Category'].str.contains(
              slots_keywords['id_outer'], case=False, na=False
          )
          & df['Season'].str.contains('夏', case=False, na=False)
      ]
      if pool_summer_outer.empty:
        # 沒有夏季適用的薄外套，直接留白
        st.session_state['id_outer'] = ''
        continue

    keyword = slots_keywords[key]
    pool = df[df['Category'].str.contains(keyword, case=False, na=False)].copy()

    if season and 'Season' in pool.columns:
      pool = pool[
          pool['Season'].str.contains(f'{season}|四季|All', case=False, na=False)
      ]

    # 套用風格強過濾
    if preset_style:
      pool = filter_by_style(pool, preset_style, key)

    # Tone-on-Tone 色系鎖定
    if (
        preset_style == 'OneTone'
        and pant_color_group
        and 'ColorGroup' in pool.columns
    ):
      c_match = pool[
          pool['ColorGroup'].isin([pant_color_group, 'Mono', 'White', 'Black'])
      ]
      if not c_match.empty:
        pool = c_match

    # ★★★ 防衝突法則：褲子為主角 (Noise >= 2) 時，上身與外套強制選素色留白 (Noise <= 1) ★★★
    if (
        pant_noise >= 2
        and key in ['id_top', 'id_outer']
        and 'Noise' in pool.columns
    ):
      clean_pool = pool[pool['Noise'] <= 1]
      if not clean_pool.empty:
        pool = clean_pool

    if not pool.empty:
      st.session_state[key] = str(pool.sample(1).iloc[0]['ID'])
    else:
      # 如果篩選後為空，外套直接留白，不強制隨機補抽
      if key == 'id_outer':
        st.session_state['id_outer'] = ''


# --- 4. 詳細資訊彈窗 ---
def show_details(row, current_id):
  if 'Name' in row and pd.notna(row['Name']):
    st.markdown(
        f"<h3 style='text-align: center; margin-bottom: 0;'>{row['Name']}</h3>",
        unsafe_allow_html=True,
    )
  if 'Brand' in row and pd.notna(row['Brand']):
    st.markdown(
        "<p style='text-align: center; color: #666; font-weight:"
        f" bold;'>{row['Brand']}</p>",
        unsafe_allow_html=True,
    )
  st.markdown('---')

  display_order = [
      ('Category', '分類'),
      ('Size', '尺寸'),
      ('Color', '顏色'),
      ('ColorGroup', '色系'),
      ('Fit', '版型'),
      ('Style', '風格'),
      ('Aesthetic', '調性'),
      ('Season', '季節'),
      ('Thickness', '厚度'),
      ('Formality', '正式度'),
      ('Noise', '細節度'),
  ]

  cols = st.columns(2)
  for i, (col_key, label_zh) in enumerate(display_order):
    if col_key in row and pd.notna(row[col_key]):
      val = row[col_key]
      if col_key == 'Thickness':
        val = f'Level {int(val)}'
      with cols[i % 2]:
        st.markdown(f'**{label_zh} ({col_key})**: {val}')

  st.markdown(
      "<p style='text-align: center; font-size: 12px; color: #999; margin-top:"
      f" 15px;'>ID: {current_id}</p>",
      unsafe_allow_html=True,
  )
  st.markdown('---')

  brand = str(row.get('Brand', ''))
  cat = str(row.get('Category', ''))
  name = str(row.get('Name', ''))
  long_q = f'{brand} {name} {cat} outfit men'
  short_q = name if name else cat
  jp_q = translate_to_jp(short_q) if HAS_TRANSLATOR else short_q

  c1, c2 = st.columns(2)
  with c1:
    st.link_button(
        '🔍 Google Inspiration',
        f'https://www.google.com/search?q={long_q}&tbm=isch',
        use_container_width=True,
    )
    st.link_button(
        f'🇯🇵 WEAR ({jp_q})',
        f'https://wear.jp/coordinate/?search_word={jp_q}',
        use_container_width=True,
    )
  with c2:
    st.link_button(
        '📌 Pinterest',
        f'https://www.pinterest.com/search/pins/?q={long_q}',
        use_container_width=True,
    )
    st.link_button(
        '📷 Instagram',
        f'https://www.instagram.com/explore/search/keyword/?q={short_q}',
        use_container_width=True,
    )


# --- 5. 清除 ---
def clear_inputs():
  for key in ['id_outer', 'id_top', 'id_pant', 'id_shoes']:
    st.session_state[key] = ''


# ==========================================
# 主介面
# ==========================================
st.sidebar.title('My Closet Studio')
app_mode = st.sidebar.radio(
    'MODE', ['Stylist (智慧穿搭)', 'Gallery (衣櫃總覽)']
)
st.sidebar.markdown('---')

for k in ['id_outer', 'id_top', 'id_pant', 'id_shoes']:
  if k not in st.session_state:
    st.session_state[k] = ''
  if f'lock_{k}' not in st.session_state:
    st.session_state[f'lock_{k}'] = False

if not any([
    st.session_state['id_outer'],
    st.session_state['id_top'],
    st.session_state['id_pant'],
    st.session_state['id_shoes'],
]) and not df.empty:
  auto_generate_advanced('CityBoy')

if app_mode == 'Stylist (智慧穿搭)':
  st.title('Stylist Room')

  tab1, tab2 = st.tabs(
      ['🌤 Seasonal (氣候/季節推薦)', '🇯🇵 Magazine Presets (雜誌風格預設)']
  )

  with tab1:
    c1, c2 = st.columns([2, 1])
    with c1:
      curr_season = get_current_season()
      season_opts = ['Spring (春)', 'Summer (夏)', 'Autumn (秋)', 'Winter (冬)']
      default_idx = {'春': 0, '夏': 1, '秋': 2, '冬': 3}.get(curr_season, 0)
      sel_season_raw = st.selectbox(
          'Season', season_opts, index=default_idx, label_visibility='collapsed'
      )
      sel_season = sel_season_raw.split('(')[1].replace(')', '')
    with c2:
      if st.button('✨ 推薦當季穿搭', use_container_width=True):
        auto_generate_advanced(preset_style=None, season=sel_season)
        st.toast(f'已生成 {sel_season} 季穿搭！')

  with tab2:
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
      st.markdown('##### 🏙️ City Boy')
      st.caption('Loose x Loose《POPEYE》')
      if st.button('Apply Look', key='btn_city', use_container_width=True):
        auto_generate_advanced('CityBoy')
        st.toast('Applied: City Boy Style')
    with c2:
      st.markdown('##### 🌿 City Minimal')
      st.caption('Clean & Fluid《UOMO》')
      if st.button('Apply Look', key='btn_minimal', use_container_width=True):
        auto_generate_advanced('Minimal')
        st.toast('Applied: City Minimal Style')
    with c3:
      st.markdown('##### 🪵 Workwear')
      st.caption('Americana《2nd》')
      if st.button('Apply Look', key='btn_work', use_container_width=True):
        auto_generate_advanced('Workwear')
        st.toast('Applied: Workwear Style')
    with c4:
      st.markdown('##### ⚡ Street Grunge')
      st.caption('Punk / Skater《GRIND》')
      if st.button('Apply Look', key='btn_grunge', use_container_width=True):
        auto_generate_advanced('Grunge')
        st.toast('Applied: Street Grunge')
    with c5:
      st.markdown('##### 🎨 Tone-on-Tone')
      st.caption('同色系漸層調和')
      if st.button('Apply Look', key='btn_one', use_container_width=True):
        auto_generate_advanced('OneTone')
        st.toast('Applied: One Tone System')

  st.markdown('---')

  # 4 格單品卡片區 (左至右：外、上、下、鞋)
  slots = [
      ('OUTER', 'id_outer'),
      ('TOP', 'id_top'),
      ('BOTTOM', 'id_pant'),
      ('SHOES', 'id_shoes'),
  ]
  cols = st.columns(4)

  for i, (label, key) in enumerate(slots):
    current_id = st.session_state[key]
    with cols[i]:
      st.markdown(f'#### {label}')
      img_path = find_image_path(current_id)
      if img_path:
        st.image(img_path, use_container_width=True)
      else:
        st.image(create_placeholder_image(), use_container_width=True)

      lock_key = f'lock_{key}'
      is_locked = st.session_state[lock_key]
      st.checkbox('🔒 Locked' if is_locked else '🔓 Unlock', key=lock_key)

      if current_id:
        with st.popover(f'Details ({current_id})', use_container_width=True):
          if not df.empty:
            info = df[df['ID'].astype(str) == current_id]
            if not info.empty:
              show_details(info.iloc[0], current_id)

  st.sidebar.header('手動指定 ID')
  for lbl, k in slots:
    st.sidebar.text_input(lbl, key=k)
  st.sidebar.button('🗑 Clear All', on_click=clear_inputs)

elif app_mode == 'Gallery (衣櫃總覽)':
  st.title('Collection Gallery')
  if df.empty:
    st.info('Please create data.xlsx first.')
  else:
    st.sidebar.header('🔍 搜尋條件')
    cats = (
        ['全部 (ALL)'] + list(df['Category'].dropna().unique())
        if 'Category' in df.columns
        else ['全部 (ALL)']
    )
    sel_cat = st.sidebar.selectbox('分類 (Category)', cats)

    colors = (
        ['全部 (ALL)'] + list(df['Color'].dropna().unique())
        if 'Color' in df.columns
        else ['全部 (ALL)']
    )
    sel_color = st.sidebar.selectbox('顏色 (Color)', colors)

    term = st.sidebar.text_input('搜尋 (編號/品名/關鍵字)', '').strip()

    res = df.copy()
    if sel_cat != '全部 (ALL)':
      res = res[res['Category'] == sel_cat]
    if sel_color != '全部 (ALL)':
      res = res[res['Color'] == sel_color]
    if term:
      mask = res.apply(
          lambda x: x.astype(str).str.contains(term, case=False).any(), axis=1
      )
      res = res[mask]

    st.markdown(f'### {len(res)} Items')
    cols = st.columns(4)
    for i, (idx, row) in enumerate(res.iterrows()):
      with cols[i % 4]:
        iid = str(row['ID'])
        path = find_image_path(iid)
        if path:
          st.image(path, use_container_width=True)
        else:
          st.image(create_placeholder_image(), use_container_width=True)
        st.caption(iid)
        with st.popover('Details', use_container_width=True):
          show_details(row, iid)