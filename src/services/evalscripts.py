def get_evalscript(bands: list[str], sampleType: str = "FLOAT32") -> str:
    bands_js = ', '.join(f'"{band}"' for band in bands)
    returns_js = ', '.join(f"sample.{band}" for band in bands)
    return f"""
        //VERSION=3

        function setup() {{
            return {{
                input: [{{
                    bands: [{bands_js}]
                }}],
                output: {{
                    bands: {len(bands)},
                    sampleType: "{sampleType}"
                }}
            }};
        }}

        function evaluatePixel(sample) {{
            return [{returns_js}];
        }}
    """