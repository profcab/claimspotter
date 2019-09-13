nohup sh -c "python3 pretrain.py --cb_output_dir=output --gpu=0 --bert_model_size=large --tfm_ft_enc_layers=2"&>nohup.out&

nohup sh -c "python3 pretrain.py --cb_output_dir=output1 --gpu=1 --bert_model_size=large --tfm_ft_enc_layers=4"&>nohup1.out&

nohup sh -c "python3 pretrain.py --cb_output_dir=output2 --gpu=2 --bert_model_size=large_wwm --tfm_ft_enc_layers=2"&>nohup2.out&

nohup sh -c "python3 pretrain.py --cb_output_dir=output3 --gpu=3 --bert_model_size=large_wwm --tfm_ft_enc_layers=4"&>nohup3.out&

nohup sh -c "python3 advtrain.py --cb_input_dir=output3/ --cb_output_dir=output1 --gpu=1 --bert_model_size=large_wwm --tfm_ft_enc_layers=2"&>nohup1.out&

nohup sh -c "python3 advtrain.py --cb_input_dir=output3/002 --cb_output_dir=output2 --gpu=2 --bert_model_size=large_wwm --tfm_ft_enc_layers=3 --kp_tfm_atten=0.8 --kp_tfm_hidden=0.8"&>nohup2.out&


nohup sh -c "python3 advtrain.py --cb_input_dir=output3/002 --cb_output_dir=output4 --gpu=3 --bert_model_size=large_wwm --tfm_ft_enc_layers=2 --kp_tfm_atten=0.8 --kp_tfm_hidden=0.8"&>nohup3.out&

nohup sh -c "python3 advtrain.py --cb_input_dir=output3/002 --cb_output_dir=output2 --gpu=2 --bert_model_size=large_wwm --tfm_ft_enc_layers=2 --kp_tfm_atten=0.6 --kp_tfm_hidden=0.6"&>nohup2.out&

nohup sh -c "python3 advtrain.py --cb_input_dir=output3/002 --cb_output_dir=output2 --gpu=2 --bert_model_size=large_wwm --tfm_ft_enc_layers=2 --kp_tfm_atten=0.7 --kp_tfm_hidden=0.7"&>nohup2.out&

nohup sh -c "python3 advtrain.py --cb_input_dir=output3/002 --cb_output_dir=output1 --gpu=1 --bert_model_size=large_wwm --tfm_ft_enc_layers=2 --kp_tfm_atten=0.7 --kp_tfm_hidden=0.7 --l2_reg_coeff=0.0"&>nohup1.out&

nohup sh -c "python3 pretrain.py --cb_output_dir=output --gpu=0 --pretrain_steps=5"&>nohup.out&

nohup sh -c "python3 advtrain.py --cb_input_dir=output --cb_output_dir=output1 --gpu=1 --perturb_id=1"&>nohup1.out&
nohup sh -c "python3 advtrain.py --cb_input_dir=output --cb_output_dir=output2 --gpu=2 --perturb_id=2"&>nohup2.out&
nohup sh -c "python3 advtrain.py --cb_input_dir=output --cb_output_dir=output3 --gpu=3 --perturb_id=3"&>nohup3.out&

python3 pretrain.py # pre-fine-tune the classifier for the claimspotting task. vanilla training on the custom  3-5 epochs
python3 advtrain.py
python3 eval.py

python3 demo.py