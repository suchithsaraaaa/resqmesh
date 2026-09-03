import os
import glob
import re

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SCREENS_FABRIC = os.path.join(PROJECT_ROOT, "mobile", "node_modules", "react-native-screens", "src", "fabric")

files_fixed = 0
for filepath in glob.glob(os.path.join(SCREENS_FABRIC, "**", "*.ts"), recursive=True):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    if "CT.WithDefault" in content or "CT." in content:
        new_content = content.replace("CT.WithDefault", "WithDefault")
        new_content = new_content.replace("CT.Int32", "Int32")
        new_content = new_content.replace("CT.Float", "Float")
        new_content = new_content.replace("CT.Double", "Double")
        new_content = new_content.replace("CT.DirectEventHandler", "DirectEventHandler")
        new_content = new_content.replace("CT.BubblingEventHandler", "BubblingEventHandler")

        # Update import statement
        if "WithDefault" in new_content and "WithDefault" not in content.split("import")[1].split("from")[0]:
            new_content = re.sub(
                r"import type \{([^}]+)\} from 'react-native';",
                r"import type { WithDefault, Int32, Float, Double, DirectEventHandler, BubblingEventHandler, \1 } from 'react-native';",
                new_content
            )

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(new_content)
        files_fixed += 1

print(f"Fixed {files_fixed} fabric component files in react-native-screens.")
