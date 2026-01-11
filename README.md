<h1><img src="/assets/reesaber_converter_icon.png" alt="ReeSaber Icon" width="110" align="center"> ReeSaber Converter</h1>

Convert Beat Saber .saber files to ReeSabers format with a single click.

## Live Site

Visit: https://stargazer6481.github.io/.saberToReesaber/

## Status

This project is currently in BETA. The converter may not work for all .saber files or may experience downtime. If you encounter issues, please try again later or report them in the issues section.

## What It Does

This tool converts custom Beat Saber sabers (.saber files) into the format used by the ReeSabers mod. It extracts meshes, textures, and generates the proper preset JSON files automatically.

## How To Use

1. Visit the live site
2. Upload your .saber file (drag and drop or click to browse)
3. Click "CONVERT"
4. Download the generated ZIP file
5. Extract to `Beat Saber/UserData/ReeSabers/`
6. Launch Beat Saber and enjoy your converted saber

## Tech Stack

- Frontend: Pure HTML/CSS/JavaScript (vibe coded)
- Backend: Python Flask + UnityPy
- Hosting: GitHub Pages + Render.com

## Requirements

- ReeSabers mod installed in Beat Saber
- A valid .saber file from custom sabers

## Known Issues

- First conversion may take 30+ seconds due to server cold start
- Very large .saber files may timeout
- Some legacy .saber formats may not be supported

## Contributing

This is a community tool. Feel free to fork and improve it.

## Credits

Vibe coded with Claude. Made for the Beat Saber community.

## License

MIT do whatever you want
