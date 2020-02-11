import os
import sys
import argparse


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--photos", help="Path to photos.", required=False)
    parser.add_argument("-x", "--xmls", help="Path to XMLs.", required=False)
    args = parser.parse_args()
    return args


def get_xml_name(photo_name):
    return photo_name.rsplit(".", maxsplit=1)[0] + ".xml"


def create_xml(path):
    with open(path, "w") as f:
        f.write("<PcGts xmlns=\"http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15\">\n"
                "   <Page>\n"
                "   </Page>\n"
                "</PcGts>")


def create_missing(photos_path, xmls_path):
    photo_names = [f for f in os.listdir(photos_path) if f.endswith(".jpg_rec.jpg")]

    for photo_name in photo_names:
        xml_name = get_xml_name(photo_name)
        xml_path = os.path.join(xmls_path, xml_name)
        if not os.path.exists(xml_path):
            create_xml(xml_path)


def main():
    args = parse_args()

    create_missing(args.photos, args.xmls)

    return 0


if __name__ == "__main__":
    sys.exit(main())
