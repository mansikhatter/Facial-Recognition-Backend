import argparse

parser = argparse.ArgumentParser(description = 'Recognize Face Image')
parser.add_argument('-indir', type=str, help='Input dir for Image')
parser.add_argument('-outdir',type=str, help='Output dir for Name')

args=parser.parse_args()
print(args.indir)