python script/cleanup_tiknib_test.py

python helper/do_idascript.py \
  --idapath "/home/user/win_workspace/IDA" \
  --idc "tiknib/ida/fetch_funcdata_v7.5.py" \
  --input_list "example/test1/list.txt"

python script/handle_pickle.py /home/user/win_workspace/storage/tiknib/test1

python helper/extract_lineno.py \
  --input_list "example/test1/list.txt" \
  --threshold 1000

python helper/filter_functions.py \
  --input_list "example/test1/list.txt" \
  --threshold 1

python helper/extract_functype.py \
    --input_list "example/test1/list.txt" \
    --source_list "example/test1/sources.txt" \
    --ctags_dir "data/test1" \
    --threshold 1

python helper/extract_features.py \
    --input_list "example/test1/list.txt" \
    --threshold 1
