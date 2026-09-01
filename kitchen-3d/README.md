# The Walkable Kitchen

A first-person, walkable 3D reconstruction of the kitchen/dining room (5.32 m x 4.56 m),
built to scale from the hand-measured sketch and the 360-degree photo sweep. Single
self-contained `index.html` (Three.js r128 from cdnjs) - no build step.

## Deploy to Netlify (one command, from this folder)

```sh
cd kitchen-3d
npx -y netlify-cli deploy --dir . --prod
```

First run opens a browser window to authorize (be logged into Netlify), then prints the
live URL. Alternative with zero tooling: drag this folder onto https://app.netlify.com/drop

## Controls

- Click to walk in: WASD / arrows move, mouse looks, Shift runs, Esc releases the mouse
- Touch: left pad walks, drag anywhere to look
- `M` plan view (top-down), `L` dimension labels, `T` tape measure (click two points),
  `F` toggle loose furniture, `B` toggle cabinets/appliances (both off = bare shell), `R` reset
