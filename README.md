# Nambulite Notch

Amber neon pinball for [ElbowOS](https://x.com/ElbowOS). Python 3 + pygame.

Flip the copper paddles and keep the ember ball off the drain. Bumper hits charge the notch gate at the top of the table. Punch the gate for a bonus.

This is an original arcade table. It is not a commercial pinball ROM and not an emulator.

## Play

```bash
pip install -r requirements.txt
python3 nambulite_notch.py --play
```

Left / A flips the left paddle. Right / D flips the right. Space launches. R restarts.

## Record a 9:16 reel

```bash
python3 nambulite_notch.py --record
```

Writes a 1080x1920 h264 clip (15s @ 30fps, yuv420p, CRF 20, +faststart) with title, score, and `x.com/ElbowOS` burned into the frames. Headless runs use `SDL_VIDEODRIVER=dummy`.

- Featured account: https://x.com/ElbowOS
- Drive reel: https://drive.google.com/file/d/19oUHQ50E7xmZ5NbqRv1iU5E0YD1riubc/view
