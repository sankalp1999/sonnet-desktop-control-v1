### WIP

Hacky code (don't judge me)

I tried to control my desktop yesterday with help of 3.5 sonnet (and failed mostly). 
I use three function calls - take a screenshot to analyze screen, move cursor and click and one to type text.
Demo can be found [here](https://x.com/dejavucoder/status/1806657345285742652)

Sonnet vision is very good but still misses buttons by a small margin. Need to find 
better methods where you can either give information about screen coordinates or totally remove the need of them 
e.g use DOM input but limited
to browsers


Lots of improvement at prompt also possible but main bottleneck right now is the Vision.


`git clone https://github.com/sankalp1999/sonnet-desktop-control-v1.git`

`python -m venv myenv`

`source venv/bin/activate`

`pip install -r requirements.txt`

