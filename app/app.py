#####################################################################
#   中部精機様向け
#   カウント数自動記録プログラム Ver.1.0 (アルミピン検査機用)
#- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
#   Last Update on 2026.9.16
#   シャフトA検査装置用プログラムを流用した
#   動作確認環境 Python Ver.3.11.1
#
#   変更するべき個所に「要変更」と記入した→変更後に消去する
#####################################################################

### インポート処理 #####################################
import tkinter as tk
import tkinter.ttk as ttk
import tkinter.messagebox as messagebox
import os
import configparser
import socket
from datetime import datetime,date,timedelta
import csv
import glob
import subprocess
import shutil

# VS Code使用時のみ必要な処理(カレントディレクトリ移動処理)
os.chdir(os.path.dirname(__file__))

### 関数定義 ###########################################
if True:
  # 加工期間/検査日テキストボックス入力処理 --------------------
  def input_date(btn):
    txt_obj = None  # Entryオブジェクト格納用
    if txtbox_pos==1:
      txt_obj = txt_from
    elif txtbox_pos==2:
      txt_obj = txt_to
    elif txtbox_pos==3:
      txt_obj = txt_date
    else:
      return

    # 押されたボタンに応じて増減させる日数を格納
    if btn=='-1':
      days = -1
    if btn=='-10':
      days = -10
    if btn=='+1':
      days = 1
    if btn=='+10':
      days = 10

    if txt_obj.get()=='':
      # テキストボックス未入力の時
      txt_obj.delete(0,tk.END)
      txt_obj.insert(tk.END,calc_date(''))  # 今日の入力
    else:
      std_date = txt_obj.get()
      txt_obj.delete(0,tk.END)
      txt_obj.insert(tk.END,calc_date(std_date,days))

    # 検査日変更時はDataID取得
    if txtbox_pos==3:
      # 検査機番選択時
      if var_insno.get()!='':
        id = get_dataid(int(var_insno.get()[0])) #引数=検査機番
        txt_id['text'] = id


  # 日付計算(基準時間から指定した日数を増減) --------------------
  def calc_date(std_date, days=0):
    if std_date=='':
      # 基準日情報なしの場合(今日の日付を戻す)
      return date.today().strftime('%Y/%m/%d')
    
    d1 = datetime.strptime(std_date,'%Y/%m/%d').date()
    delta = timedelta(days=days)
    d2 = d1 + delta
    return d2.strftime('%Y/%m/%d')


  # 日付用テキストボックス記憶(クリック時) --------------------
  def set_txtpos1(e):
    global txtbox_pos; txtbox_pos = 1
  def set_txtpos2(e):
    global txtbox_pos; txtbox_pos = 2
  def set_txtpos3(e):
    global txtbox_pos; txtbox_pos = 3


  # アプリ立ち上げ時処理 --------------------
  def init_proc():
    #必要ファイル/フォルダ有無確認
    for i in range(InsMcNum):
      output_folder = './DATA/MC' + str(i+1)
      if not os.path.isdir(output_folder):
        messagebox.showwarning(message='データ出力用フォルダがありません')
        exit()   
    if not os.path.isfile('MachineNo.csv'):
      messagebox.showwarning(message='機械Noファイルが見つかりません。')
      exit()
    if not os.path.isfile('config.ini'):
      messagebox.showwarning(message='configファイルが見つかりません。')
      exit()
    #CONFIGファイル読み込み
    config = configparser.ConfigParser()
    config.read('config.ini')
    global ip_address
    for i in range(InsMcNum):
      ip_address.append(config.get('ip_address',f'mc{i+1}'))
    # print(ip_address) # ForDebug


  # 加工機番データ(CSV)をリストで戻す処理 --------------------
  def read_mcno(file_name):
    with open(file_name,'r') as f:
      lst = [x.rstrip() for x in f.readlines()]
    return lst


  # PLC通信処理 ------------------------------
  def get_from_plc(ip,device):
    ipadd = ip
    port = 8501
    server = (ipadd, port)
    skt = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    skt.settimeout(3) # Timeoutを3secに設定(無設定だと約20sec)
    try:
      skt.connect(server)
      # 通信
      msg = 'RD ' + device + '\r'
      skt.send(msg.encode('ASCII'))
      rcv = skt.recv(8192).decode().rstrip()
      rcv = str(int(rcv)) # ゼロサプレス
      skt.close()
      return rcv
    except:
      messagebox.showerror('エラー','PLCと通信できません')
      return


  # PLCカウント数クリア処理 ------------------(要変更->リセットデバイス数)
  def clear_plc_count(ip):
    ipadd = ip
    port = 8501
    server = (ipadd, port)
    skt = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    skt.settimeout(3) # Timeoutを3secに設定(無設定だと約20sec)
    try:
      skt.connect(server)
      # 通信
      msg = 'WRS DM602.D 10 0 0 0 0 0 0 0 0 0 0\r'   # DM602から10個分0格納
      skt.send(msg.encode('ASCII'))
      rcv = skt.recv(8192).decode().rstrip()
      print(f'response={rcv}')
      skt.close()
    except:
      messagebox.showerror('エラー','PLCと通信できません')
      return


  # PLCカウント数 入力処理 --------------------(要変更)
  def input_count_val():
    if var_insno.get()=='':
      messagebox.showwarning('エラー','検査機番が選択されていません')
      return    
    # IPアドレス設定
    insno = int(var_insno.get()) # Combobox検査機選択値
    ipadd = ip_address[insno-1]
    
    # 検査数格納
    val = get_from_plc(ipadd,'DM602.D')
    txt_total.delete(0,tk.END); txt_total.insert(tk.END,val)
    # OK数格納
    val = get_from_plc(ipadd,'DM604.D')
    txt_ok.delete(0,tk.END); txt_ok.insert(tk.END,val)
    # NG1(形状NG)数格納
    val = get_from_plc(ipadd,'DM612.D')
    txt_ng1.delete(0,tk.END); txt_ng1.insert(tk.END,val)
    # NG2(側面NG)数格納
    val = get_from_plc(ipadd,'DM614.D')
    txt_ng2.delete(0,tk.END); txt_ng2.insert(tk.END,val)
    # NG3(端面NG)数格納
    val = get_from_plc(ipadd,'DM616.D')
    txt_ng3.delete(0,tk.END); txt_ng3.insert(tk.END,val)
    # NG4(全長NG)数格納
    val = get_from_plc(ipadd,'DM618.D')
    txt_ng4.delete(0,tk.END); txt_ng4.insert(tk.END,val)
    # NG5(予備NG)数格納
    val = get_from_plc(ipadd,'DM620.D')
    val = 0 # ＜注＞ 使用する時に削除すること
    txt_ng5.delete(0,tk.END); txt_ng5.insert(tk.END,val)
    # NG6(予備NG)数格納
    val = get_from_plc(ipadd,'DM620.D')
    val = 0 # ＜注＞ 使用する時に削除すること
    txt_ng6.delete(0,tk.END); txt_ng6.insert(tk.END,val)


  # 入力エリア クリア処理 --------------------
  def clear_data():
    global modify_flg
    if modify_flg==True:  # データ修正モード時
      modify_flg=False; lbl_modify['text']=''
      cmb_mcno2['state'] = 'normal'
      txt_date['state'] = 'normal'

    txt_id['text'] = ''         # データID
    var_mcno.set('')            # 加工機番
    # txt_from.delete(0,tk.END)   # 加工日開始
    # txt_to.delete(0,tk.END)     # 加工日終了
    # txt_date.delete(0,tk.END)   # 検査日
    txt_total.delete(0,tk.END)  # 検査数
    txt_ok.delete(0,tk.END)     # OK数
    txt_ng1.delete(0,tk.END)    # NG1数
    txt_ng2.delete(0,tk.END)    # NG2数
    txt_ng3.delete(0,tk.END)    # NG3数
    txt_ng4.delete(0,tk.END)    # NG4数
    txt_ng5.delete(0,tk.END)    # NG5数
    txt_ng6.delete(0,tk.END)    # NG6数
    txt_note.delete(0,tk.END)   # 備考
    # var_insno.set('           # 検査機番→クリアしない方が操作性良い

    # データID取得(検査機番と検査日をクリアしないため必要)
    if var_insno.get()!='' and txt_date.get()!='':
      id = get_dataid(int(var_insno.get()[0]))  #引数:検査機番
      txt_id['text'] = id

  # 検査機番コンボボックス変更時処理 --------------------
  def cmb_mcno2_changed(e):
    mc_no = var_insno.get()[0] # Combobox選択中の検査機番
    str_today = str(date.today()).replace('-','/') 
    fpath = get_csv_path(mc_no, str_today)
    disp_csvdata(fpath)

    # DataIDの更新
    if txt_date.get()!='':  # 検査日が入力されている時
      id = get_dataid(int(var_insno.get()[0])) #引数=検査機番
      txt_id['text'] = id


  # CSVデータのTreeview表示処理 --------------------
  def disp_csvdata(fpath):
    global disp_fpath
    # Treeview全データ削除
    for id in tree.get_children():
      tree.delete(id)
    # CSVファイル有無確認
    if not os.path.isfile(fpath):
      disp_fpath = ''
      frame2['text'] = 'データ一覧：(ファイルなし)'
      return
    # CSVファイル読取
    with open(fpath,'r') as f:
      data = [line for line in csv.reader(f)]
    data = data[1:] # 1行目のヘッダ行除去
    
    if len(data)==0:  # ヘッダ行だけの場合終了
      return
    # レコード追加
    for x in data:
      tree.insert('','end',values=x)
    # フレームタイトルへファイル名表示
    disp_fpath = fpath
    frame2['text'] = 'データ一覧：'+os.path.basename(disp_fpath)
    # Treeview最終アイテムを表示
    last_item = tree.get_children()[len(tree.get_children())-1]
    tree.see(last_item)


  # DataID取得処理 --------------------
  def get_dataid(mcno):
    # 検査日Entryと検査機番Combobox変更時に呼び出される
    if modify_flg==True:  # データ修正時は現在値を戻す
      return txt_id['text']
    insdate = txt_date.get()  # 検査日Entry入力内容
    fpath = get_csv_path(mcno,insdate)
    if os.path.isfile(fpath): # ファイルある場合
      data = get_list_from_csv(fpath)
      if len(data)==0:  # ヘッダ行だけの場合
        s = insdate[2:7].replace('/','') + '-' + '0001'
        return s
      else: # データが存在する場合
        maxid = max(data)[0]  # 最大のDataID取得
        s = maxid[:5] + str(int(maxid[-4:]) + 1).zfill(4) # 下4桁インクリメント
        return s
    else: # ファイルない場合
      s = insdate[2:7].replace('/','') + '-' + '0001'
      return s


  # CSVファイルからデータをリストとして取得 --------------------
  def get_list_from_csv(fpath):
    with open(fpath,'r') as f:
      data = [line for line in csv.reader(f)]
    data = data[1:] # 1行目のヘッダ行除去
    return data

  
  # データ登録処理 --------------------
  def regist_data():
    # 入力チェック
    if check_inputbox()==False:
      messagebox.showerror('エラー','入力値が不正です')
      return
    # 現在入力データ取得
    lst = get_present_data()
    print(f'lst={lst}')
    # 出力ファイル有無確認
    mc_no = var_insno.get()[0]  # Combobox1文字目
    ins_date = txt_date.get()   # 検査日
    fpath = get_csv_path(mc_no,ins_date) #CSVファイルパス
    
    if os.path.isfile(fpath): # ファイル存在する場合
      # DataIDが既に登録されているか
      if not find_dataID(lst[0],fpath): # 新規データとして追加
        print('appending new data')
        with open(fpath,'a',newline='') as f:
          writer = csv.writer(f)
          writer.writerow(lst)
      else: # 既存データの修正
        print('modifying data')
        # CSVファイル読取
        with open(fpath,'r') as f:
          data = [line for line in csv.reader(f)]
        # 該当データ入れ替え
        for i,x in enumerate(data):
          if x[0]==lst[0]:  # DataIDが一致する行の場合
            data[i] = lst #データ入れ替え
        # 新規ファイルとして保存(上書)
        with open(fpath,'w',newline='') as f:
          writer = csv.writer(f)
          writer.writerows(data)
    else:
      # ファイル存在しない場合→新規作成
      print('creating new file & new data')
      with open(fpath,'w',newline='') as f:
        writer = csv.writer(f)
        writer.writerow(HEADER)
        writer.writerow(lst)

    # PLCカウンタ0リセット(データ修正時は非実行)
    if modify_flg == False:
      res = messagebox.askyesno('確認','PLCのカウンタをリセットしますか？')
      if res==True:
        # IPアドレス設定
        insno = int(var_insno.get()) # Combobox検査機選択値
        ipadd = ip_address[insno-1]
        clear_plc_count(ipadd)

    disp_csvdata(fpath) #Treeview更新
    clear_data()    #入力ボックスリセット


  # CSVファイル内に既にDataIDが登録されているか調べる ---------------
  def find_dataID(id,fpath):
    # CSVファイル読取
    with open(fpath,'r') as f:
      data = [line for line in csv.reader(f)]
    data = data[1:] # 1行目のヘッダ行除去
    ids = [x[0] for x in data]  # DataIDだけのリスト
    return id in ids  # 戻り値:True/False


  # 現在データの取得 --------------------
  def get_present_data():
    lst = []
    lst.append(txt_id['text'])    # DataID
    lst.append(var_mcno.get())    # 加工機番
    lst.append(txt_from.get())    # 加工日開始
    lst.append(txt_to.get())      # 加工日終了
    lst.append(var_insno.get())   # 検査機番
    lst.append(txt_date.get())    # 検査日
    lst.append(txt_total.get())   # 検査数
    lst.append(txt_ok.get())      # OK数
    lst.append(txt_ng1.get())     # NG1数
    lst.append(txt_ng2.get())     # NG2数
    lst.append(txt_ng3.get())     # NG3数
    lst.append(txt_ng4.get())     # NG4数
    lst.append(txt_ng5.get())     # NG5数
    lst.append(txt_ng6.get())     # NG6数
    lst.append(txt_note.get())    # 備考
    return lst


  # CSVファイルパス取得(引数：検査機番,検査日) --------------------
  def get_csv_path(mc_no,ins_date):
    # mc_no : 1-3(int型)
    # ins_date : YYYY/mm/dd(str型)
    fname = 'MC' + str(mc_no) + '_' + ins_date[:7].replace('/','') \
          + '.CSV'
    folder='./DATA/MC' + str(mc_no) + '/'
    fpath = folder + fname
    return fpath


  # 前月データ表示 --------------------
  def disp_prev_month():
    if var_insno.get()=='': # 検査機番未選択時
      return
    mc_no = cmb_mcno2.get()  # 検査機番
    folder = './DATA/MC' + str(mc_no) + '/'
    files = glob.glob(folder + 'MC*.CSV')
    if len(files)==0:
      return
    else:
      files = [f.replace('\\','/') for f in files] #「\\」を「/」に置換

    if disp_fpath in files:
      # 表示データがfilesに存在する時、1つ前のデータ表示  
      idx = files.index(disp_fpath)
      if idx!=0:
        disp_csvdata(files[idx-1])
    else:
      # 表示データがfilesに存在しない時、最新データ表示
      # (現在日に最も近い前のデータが理想だが、煩雑になるため不採用)
      disp_csvdata(files[len(files)-1])


  # 当月データ表示 --------------------
  def disp_this_month():
    if var_insno.get()=='': # 検査機番未選択時
      return
    mc_no = cmb_mcno2.get()
    str_today = str(date.today()).replace('-','/')
    fpath = get_csv_path(mc_no, str_today)
    disp_csvdata(fpath)


  # 翌月データ表示 --------------------
  # (前月データ表示処理とほとんど同じなので関数化を検討すること)
  def disp_next_month():
    if var_insno.get()=='': # 検査機番未選択時
      return
    mc_no = cmb_mcno2.get()  # 検査機番(数字のみ)
    folder = './DATA/MC' + str(mc_no) + '/'
    files = glob.glob(folder + 'MC*.CSV')
    if len(files)==0:
      return
    else:
      files = [f.replace('\\','/') for f in files] #「\\」を「/」に置換

    if disp_fpath in files:
      # 表示データがfilesに存在する時、1つ後のデータ表示  
      idx = files.index(disp_fpath)
      if idx!=len(files)-1: #最終インデックスでない場合
        disp_csvdata(files[idx+1])
    else:
      # 表示データがfilesに存在しない時、最新データ表示
      # (現在日に最も近い後のデータが理想だが、煩雑になるため不採用)
      disp_csvdata(files[len(files)-1])


# 選択されたデータを入力ボックスへ移動 ---------------------
  def input_modifydata():
    id = tree.focus() # Treeview
    if id=='':
      messagebox.showwarning('エラー','データが選択されていません')
      return
    val = list(tree.item(id,'values'))  # 選択行データ取得
    clear_data()  # 入力ボックス クリア
    # 加工日と検査日はクリアする必要あり(2023.6.16修正)
    txt_from.delete(0,tk.END)   # 加工日開始
    txt_to.delete(0,tk.END)     # 加工日終了
    txt_date.delete(0,tk.END)   # 検査日
    
    # print(val)  #ForDebug
    txt_id['text'] = val[0] # DataID
    var_mcno.set(val[1])    # 加工機番
    txt_from.insert(tk.END,val[2])    # 加工日開始
    txt_to.insert(tk.END,val[3])      # 加工日終了
    var_insno.set(val[4])             # 検査機番
    txt_date.insert(tk.END,val[5])    # 検査日
    txt_total.insert(tk.END,val[6])   # 検査数
    txt_ok.insert(tk.END,val[7])      # OK数
    txt_ng1.insert(tk.END,val[8])     # NG1数
    txt_ng2.insert(tk.END,val[9])     # NG2数
    txt_ng3.insert(tk.END,val[10])    # NG3数
    txt_ng4.insert(tk.END,val[11])    # NG4数
    txt_ng5.insert(tk.END,val[12])    # NG5数
    txt_ng6.insert(tk.END,val[13])    # NG6数
    txt_note.insert(tk.END,val[14])   # 備考
    # 修整中フラグセット＆ラベル表示
    global modify_flg
    modify_flg=True; lbl_modify['text']='--- 修整中 ---'
    cmb_mcno2['state'] = 'disable'
    txt_date['state'] = 'disable'


  # Treeview選択データの削除 ---------------
  def remove_data():
    # 選択行のDataID取得
    id = tree.focus() # Treeview
    if id=='':
      messagebox.showwarning('エラー','データが選択されていません')
      return
    val = list(tree.item(id,'values'))  # 選択行データ取得
    ans = messagebox.askyesno('確認',f'DataID = {val[0]}を削除しますか？')
    if ans==False:
      return
    
    fpath = disp_fpath  # 現在Treeview表示中のCSVファイル
    # CSVファイル読取
    with open(fpath,'r') as f:
      data = [line for line in csv.reader(f)]
    # 該当データ入れ替え
    for i,x in enumerate(data):
      if x[0]==val[0]:    # DataIDが一致する行の場合
        data.pop(i)  #データ削除
    # 新規ファイルとして保存(上書)
    with open(fpath,'w',newline='') as f:
      writer = csv.writer(f)
      writer.writerows(data)
    
    disp_csvdata(fpath) #Treeview更新


  # データ登録前の入力値チェック ----------------
  def check_inputbox():
    # 空欄チェック
    if txt_id['text']=='':  # DataID
      return False
    if var_mcno.get()=='':  # 加工機番
      return False
    if txt_from.get()=='':  # 加工日開始
      return False
    if txt_to.get()=='':    # 加工日終了
      return False
    if txt_date.get()=='':  # 検査日
      return False
    if var_insno.get()=='': # 検査機番
      return False
    if txt_total.get()=='': # 検査数
      return False
    if txt_ok.get()=='':    # OK数
      return False
    if txt_ng1.get()=='':   # NG1数
      return False
    if txt_ng2.get()=='':   # NG2数
      return  False
    if txt_ng3.get()=='':   # NG3数
      return False
    if txt_ng4.get()=='':   # NG4数
      return False
    if txt_ng5.get()=='':   # NG5数
      return False
    if txt_ng6.get()=='':   # NG6数
      return False
    # 日付チェック(datetime型に変換できるかで判断)
    try:
      d = datetime.strptime(txt_from.get(),'%Y/%m/%d')
      d = datetime.strptime(txt_to.get(),'%Y/%m/%d')
      d = datetime.strptime(txt_date.get(),'%Y/%m/%d')
    except:
      print('日付データ異常')
      return False
    
    # 数字チェックl(int型に変換できるかで判断)
    try:
      n = int(txt_total.get())
      n = int(txt_ok.get())
      n = int(txt_ng1.get())
      n = int(txt_ng2.get())
      n = int(txt_ng3.get())
      n = int(txt_ng4.get())
      n = int(txt_ng5.get())
      n = int(txt_ng6.get())
    except:
      print('カウント数 入力値異常')
      return False
    
    return True  # 正常時

  # HELPファイルの表示 ---------------
  def disp_help():
    subprocess.Popen(['start','HELP.pdf'],shell=True)
    # 参考→https://tonari-it.com/python-popen-start-folder/


  # バックアップ用サブウィンドウ表示 ----------------------------
  def create_buwindow():
    global buwin
    # Windowの2重生成禁止
    if buwin!=None:
      if buwin.winfo_exists():
        return

      
    # --- サブフォーム関数定義 ----------------------------
    # バックアップ処理
    def excute_backup():
      drive = var_drv.get()
      bu_target = var_butarget.get()
      print(drive,bu_target)  # ForDebug
      # 入力チェック
      if input_check(drive,bu_target)==False:
        return
      # バックアップフォルダのパス格納
      foldername = 'Backup_'+datetime.now().strftime('%Y%m%d_%H%M%S')
      folderpath = drive+'/'+foldername
      # バックアップ実行
      if bu_target==1:    # 全ファイル対象
        backup_all(folderpath)
      elif bu_target==2:  # 最新ファイルのみ
        backup_latest(folderpath)
      messagebox.showinfo('メッセージ','バックアップ完了しました。')


    # 全てのファイルバックアップ処理
    def backup_all(bu_folder):
      # folderで指定されたフォルダが作成される
      shutil.copytree('./DATA',bu_folder)

    
    # 最新ファイルのみのバックアップ処理
    def backup_latest(bu_folder): # bu_folder:バックアップ先フォルダ
      os.makedirs(bu_folder)  # バックアップ用フォルダ作成
      for n in range(3):
        # 最新ファイルパスの取得(MC1-M3フォルダ対象)
        latestf = get_latestfile('./DATA/MC'+str(n+1)+'/')   # 最新ファイルパス
        if latestf!=None:
          print('latestf',latestf)
          shutil.copy2(latestf, bu_folder)


    # 最新ファイル名取得処理 ----------
    def get_latestfile(folder):
      files = glob.glob(folder + 'MC*.CSV')
      if len(files)==0:
        return
      else:
        files = [f.replace('\\','/') for f in files] #「\\」を「/」に置換
      files.sort(reverse=True)
      return files[0]


    # 必要項目選択確認処理 -------------------
    def input_check(drive,target):
      # ドライブ選択確認＆有無確認
      if drive=='':
        messagebox.showwarning('エラー','ドライブ選択してください')
        return False
      else:
        if os.path.isdir(drive)==False:
          messagebox.showwarning('エラー','ドライブが存在しません。')
          return False
      # バックアップ対象選択確認    
      if target!=1 and target!=2:
        messagebox.showwarning('エラー','バックアップ対象を選択して下さい')
        return False
      return True


    # ---バックアップウィンドウ生成 --------------------------
    buwin = tk.Toplevel()
    buwin.geometry('360x200+600+500')
    buwin.resizable(height=False,width=False) #サイズ変更禁止
    buwin.grab_set()  # ウィンドウのモーダル化
    buwin.title('データバックアップ')
    # ドライブ選択：Label&Combobox
    tk.Label(buwin,text='バックアップ先ドライブ：',font=('',12)).place(x=20,y=20)
    var_drv = tk.StringVar()
    cmb_drv = ttk.Combobox(buwin,width=7,font=('',12),state='readonly',
                           textvariable=var_drv,values=['D:','E:','F:','G:'])
    cmb_drv.place(x=230,y=20)
    # バックアップ対象選択：LabelFrame+Radiobutton x2
    bu_frame = ttk.Labelframe(buwin,text='バックアップ対象選択',
                              width=320,height=80)
    bu_frame.place(x=20,y=60)
    var_butarget = tk.IntVar()
    tk.Radiobutton(bu_frame,value=1,variable=var_butarget,
                   text='全データ',font=('',12)).place(x=20,y=10)
    tk.Radiobutton(bu_frame,value=2,variable=var_butarget,
                   text='最新ファイルのみ',font=('',12)).place(x=140,y=10)
    # 実行＆閉じるボタン：BUtton x2
    btn_excute = ttk.Button(buwin,text='実行',command=excute_backup)
    btn_excute.place(x=110,y=155)
    btn_close = ttk.Button(buwin,text='閉じる',command=lambda:buwin.destroy())
    btn_close.place(x=230,y=155)
#-- 関数定義ここまで -----------------------------------



### グローバル変数＆定数 ##################################
debug = True
ip_address = []
txtbox_pos = 0
disp_fpath = ''  # Treeview表示中ファイル名
modify_flg = False  # データ編集中フラグ
buwin = None    # バックアップ用ウィンドウ
# データ定義(CSVファイル先頭とTreeviewヘッダで使用) (要変更)
HEADER = ['DataID','加工機番','加工日開始','加工日終了','検査機番','検査日',
          '検査数','OK数','形状NG','側面NG','端面NG','全長NG','予備1','予備2','備考']
InsMcNum = 1  # 対象検査機台数

##### フォームデザイン処理 ##########################################
#--- メインウィンドウ作成 ---
root = tk.Tk()
root.title('シャフトA検査装置 カウント数自動記録アプリVer1.00')
root.geometry('1536x820') # ディスプレイ1920x1080(125%)
root.iconphoto(False,tk.PhotoImage(file='icon.png'))  # アイコン設定
root.state('zoomed')  # ウィンドウ最大化

#--- メニューバー作成 ---
menubar = tk.Menu(root)
root.config(menu=menubar)
#- 「操作」メニュー
ope_menu = tk.Menu(menubar,tearoff=0)
menubar.add_cascade(label='操作',menu=ope_menu)
ope_menu.add_command(label='閉じる',command=lambda:root.destroy())
#- 「ヘルプ」メニュー
help_menu = tk.Menu(menubar,tearoff=0)
menubar.add_cascade(label='ヘルプ',menu=help_menu)
help_menu.add_command(label='ヘルプ表示',command=disp_help)

#--- 上部デザイン ----
if True:
  # ttkスタイル定義
  style = ttk.Style()

  # Entryを高くする
  style.configure('TEntry', padding=(3, 7))
  # Combobox本体を高くする
  style.configure('TCombobox', padding=(3, 7))
  # Comboboxを開いたときのリストを高くする
  root.option_add('*TCombobox*Listbox.font', ('', 16))
  # Buttonを高くする
  style.configure('TButton', font=('',12), padding=(3, 5))

  style.configure('TLabelframe.Label',font=('',12))
  style.configure('Treeview.Heading', font=('',12))
  style.configure('Treeview', font=('',12))
  style.configure('Treeview', rowheight=30)
  
  # 上部フレーム --------------------------------------------------------------------
  frame1 = ttk.Labelframe(root,text='登録用データ',width=1500,height=180,style='TLabelframe')
  frame1.pack(padx=10,pady=10)
  # 1行目 ----------
  # データID:Labelx2(txt_idは手動入力不可にするためEntryからLabelに変更)
  tk.Label(frame1,text='データID：',font=('',12)).place(x=10,y=10)
  txt_id = ttk.Label(frame1,text='',font=('',12),relief='solid',
                     width=11,anchor=tk.CENTER)
  txt_id.place(x=100,y=10)
  # 加工機番:Label&Combobox
  tk.Label(frame1,text='加工機番：',font=('',12)).place(x=220,y=10)
  var_mcno = tk.StringVar()
  cmb_list = read_mcno('MachineNo.csv')
  cmb_mcno = ttk.Combobox(frame1,width=7,font=('',12),state='readonly',
                          textvariable=var_mcno,values=cmb_list)
  cmb_mcno.place(x=310,y=10)
  # 加工期間:Label&Entry x2
  tk.Label(frame1,text='加工期間：',font=('',12)).place(x=450,y=10)
  txt_from = ttk.Entry(frame1,width=12,font=('',12),justify=tk.CENTER)
  txt_from.place(x=540,y=10)
  txt_from.bind('<FocusIn>',set_txtpos1)
  tk.Label(frame1,text='-',font=('',12)).place(x=665,y=10)
  txt_to = ttk.Entry(frame1,width=12,font=('',12),justify=tk.CENTER)
  txt_to.place(x=690,y=10)
  txt_to.bind('<FocusIn>',set_txtpos2)
  # 検査日:Label&Entry
  tk.Label(frame1,text='  検査日：',font=('',12)).place(x=820,y=10)
  txt_date = ttk.Entry(frame1,width=12,font=('',12),justify=tk.CENTER)
  txt_date.place(x=900,y=10)
  txt_date.bind('<FocusIn>',set_txtpos3)
  # データ修正中ラベル:Labl
  lbl_modify = tk.Label(frame1,text='',font=('',12),fg='red')
  lbl_modify.place(x=1030,y=10)

  # 日付入力ボタン:Button x4
  btn_minus10 = ttk.Button(frame1,text='-10',width=7)
  btn_minus10.place(x=1160,y=10)
  btn_minus10.config(command=lambda:input_date('-10'))
  btn_minus1 = ttk.Button(frame1,text='-1',width=7)
  btn_minus1.place(x=1240,y=10)
  btn_minus1.config(command=lambda:input_date('-1'))
  btn_plus1 = ttk.Button(frame1,text='+1',width=7)
  btn_plus1.place(x=1320,y=10)
  btn_plus1.config(command=lambda:input_date('+1'))
  btn_plus10 = ttk.Button(frame1,text='+10',width=7)
  btn_plus10.place(x=1400,y=10)
  btn_plus10.config(command=lambda:input_date('+10'))

  # 2行目 ----------
  # 検査数:Label & Entry (要変更)
  org2_lbl = 10     # 配置用起点(ラベル用)
  org2_txt = 84     # 配置用起点(コンボボックス用)
  pitch2 = 139      # 配置用間隔(X方向)
  tk.Label(frame1,text='検査数：',font=('',12)).place(x=org2_lbl+pitch2*0,y=60)
  txt_total = ttk.Entry(frame1,width=6,font=('',12),justify='right')
  txt_total.place(x=org2_txt+pitch2*0,y=60)
  # OK数:Label & Entry
  tk.Label(frame1,text=' O K 数：',font=('',12)).place(x=org2_lbl+pitch2*1,y=60)
  txt_ok = ttk.Entry(frame1,width=6,font=('',12),justify='right')
  txt_ok.place(x=org2_txt+pitch2*1,y=60)
  # NG1:Label & Entry
  tk.Label(frame1,text='形状NG：',font=('',12)).place(x=org2_lbl+pitch2*2,y=60)
  txt_ng1 = ttk.Entry(frame1,width=6,font=('',12),justify='right')
  txt_ng1.place(x=org2_txt+pitch2*2,y=60)
  # NG2:Label & Entry
  tk.Label(frame1,text='側面NG：',font=('',12)).place(x=org2_lbl+pitch2*3,y=60)
  txt_ng2 = ttk.Entry(frame1,width=6,font=('',12),justify='right')
  txt_ng2.place(x=org2_txt+pitch2*3,y=60)
  # NG3:Label & Entry
  tk.Label(frame1,text='端面NG：',font=('',12)).place(x=org2_lbl+pitch2*4,y=60)
  txt_ng3 = ttk.Entry(frame1,width=6,font=('',12),justify='right')
  txt_ng3.place(x=org2_txt+pitch2*4,y=60)
  # NG4:Label & Entry
  tk.Label(frame1,text='全長NG：',font=('',12)).place(x=org2_lbl+pitch2*5,y=60)
  txt_ng4 = ttk.Entry(frame1,width=6,font=('',12),justify='right')
  txt_ng4.place(x=org2_txt+pitch2*5,y=60)
  # NG5:Label & Entry
  tk.Label(frame1,text='  予備 1：',font=('',12)).place(x=org2_lbl+pitch2*6,y=60)
  txt_ng5 = ttk.Entry(frame1,width=6,font=('',12),justify='right')
  txt_ng5.place(x=org2_txt+pitch2*6,y=60)
  # NG6:Label & Entry
  tk.Label(frame1,text=' 予備 2：',font=('',12)).place(x=org2_lbl+pitch2*7,y=60)
  txt_ng6 = ttk.Entry(frame1,width=6,font=('',12),justify='right')
  txt_ng6.place(x=org2_txt+pitch2*7,y=60)

  # 検査機番:Label&Combobox
  tk.Label(frame1,text='検査機番：',font=('',12)).place(x=1160,y=60)
  var_insno = tk.StringVar()
  cmb_list = [str(n+1) for n in range(InsMcNum)]
  cmb_mcno2 = ttk.Combobox(frame1,width=7,font=('',12),state='readonly',
                           textvariable=var_insno,values=cmb_list)
  cmb_mcno2.place(x=1250,y=60)
  cmb_mcno2.bind('<<ComboboxSelected>>',cmb_mcno2_changed)
  cmb_mcno2.set("1")  # 初期値設定(不要な場合はコメントアウトする)
  
  # 3行目 ----------
  # 備考:Label & Entry
  tk.Label(frame1,text='備 考 ：',font=('',12)).place(x=10,y=110)
  txt_note = ttk.Entry(frame1,width=115,font=('',12))
  txt_note.place(x=80,y=110)
    # PLC読込:Button
  btn_plc = ttk.Button(frame1,text='PLC読込',width=10)
  btn_plc.place(x=1160,y=110)
  btn_plc.config(command=input_count_val)
  # クリア:Button
  btn_clear = ttk.Button(frame1,text='クリア',width=10)
  btn_clear.place(x=1267,y=110)
  btn_clear.config(command=clear_data)
  # データ登録:Button
  btn_regist = ttk.Button(frame1,text='データ登録',width=10)
  btn_regist.place(x=1375,y=110)
  btn_regist.config(command=regist_data)

  # 下部フレーム --------------------------------------------------------------------
  frame2 = ttk.Labelframe(root,text='データ一覧：',width=1500,height=565,style='TLabelframe')
  frame2.pack(padx=10,pady=10)

  # 列の識別名設定(識別名は後から使わないので単なる数字とする)
  clm_id = [n for n in range (15)]
  # Treeview生成
  tree = ttk.Treeview(frame2,columns=clm_id,show='headings',height=15)
  tree.place(x=10,y=10)
  # 列の見出し設定(CSVファイル1行目を利用)
  for n,id in enumerate(clm_id):
    tree.heading(id, text=HEADER[n])
  # 列幅&書式設定(データ構造に依存)
  tree.column(0,anchor='center',width=110)   # DataID
  tree.column(1,anchor='center',width=80)    # 加工機番 
  tree.column(2,anchor='center',width=120)   # 加工日開始  
  tree.column(3,anchor='center',width=120)   # 加工日終了
  tree.column(4,anchor='center',width=80)    # 検査機番
  tree.column(5,anchor='center',width=120)   # 検査日
  tree.column(6,anchor='center',width=70)    # 検査数   
  tree.column(7,anchor='center',width=70)    # OK数
  tree.column(8,anchor='center',width=70)    # NG1
  tree.column(9,anchor='center',width=70)    # NG2
  tree.column(10,anchor='center',width=70)   # NG3
  tree.column(11,anchor='center',width=70)   # NG4
  tree.column(12,anchor='center',width=70)   # NG5
  tree.column(13,anchor='center',width=70)   # NG6
  tree.column(14,anchor='w',width=250)       # 備考
  # スクロールバー追加(位置・高さは手動でTreeviewに合わせる)
  scb = ttk.Scrollbar(frame2,orient=tk.VERTICAL,command=tree.yview)
  tree.configure(yscroll=scb.set)
  scb.place(x=1465,y=10,height=475)

  # データ修正:Button
  btn_modify = ttk.Button(frame2,text='データ修正',width=10)
  btn_modify.place(x=10,y=500)
  btn_modify.config(command=input_modifydata)
  # データ削除:Button
  btn_remove = ttk.Button(frame2,text='データ削除',width=10)
  btn_remove.place(x=117,y=500)
  btn_remove.config(command=remove_data)
  # バックアップ:Button
  btn_backup = ttk.Button(frame2,text='BackUp',width=10)
  btn_backup.place(x=224,y=500)
  btn_backup.config(command=create_buwindow)

  # 前月PB:Button
  btn_prev_m = ttk.Button(frame2,text='前月',width=10)
  btn_prev_m.place(x=1160,y=500)
  btn_prev_m.config(command=disp_prev_month)
  # 当月PB:Button
  btn_this_m = ttk.Button(frame2,text='当月',width=10)
  btn_this_m.place(x=1267,y=500)
  btn_this_m.config(command=disp_this_month)
  # 次月PB:Button
  btn_next_m = ttk.Button(frame2,text='次月',width=10)
  btn_next_m.place(x=1375,y=500)
  btn_next_m.config(command=disp_next_month)
# <以上フォームデザイン処理> --------------------------------

###### メイン処理開始 ######################################################

#--- 起動時処理 ---
init_proc()

#--- メインループ ----
root.mainloop()




### MEMO ############################################################
# テキストボックス(Entry)変更時のイベントが利用できるか調査する
# → 標準では用意さていないが、以下のサイトでは自作している
# → https://qiita.com/haruyan_hopemucci/items/6718188c7820336e6900
#
# ボタン押下の処理中にメッセージボックスを表示させると青色になったままになる
# 解決策1→https://teratail.com/questions/242953 
#        (これだとaskyesnoなどの戻り値が使えない)
# 解決策2→bind命令ではなく、オプションcommandでバインドする (採用)
#  →引数を渡すときはlambdaを使用することに注意する
#  →参考：https://www.earthlink.co.jp/engineerblog/technology-engineerblog/7744/
# 解決策3→pyautoguiのメッセージボックスを使う
#
# ウィンドウ閉じるボタン押下時のイベント処理
# 参考→https://office54.net/python/tkinter/window-close-catch
#
# サブフォーム作成方法
# 参考→https://office54.net/python/tkinter/window-create-toplevel
#
# 

