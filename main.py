from PIL import Image
from PIL.ExifTags import TAGS
from iptcinfo3 import IPTCInfo
from prettytable import PrettyTable
import pyexiv2
import csv
import folium
import piexif
from colorama import Fore, Style


# Remove
def remove_metadata():
    def remove(img):
        image = Image.open(img)
        data = list(image.getdata())
        clean_data = []

        #EXIF
        try:
            info = image._getexif()
            if info:
                for tag, value in info.items():
                    tag_name = TAGS.get(tag, tag)
                    if tag_name != 'MakerNote':
                        image.info.pop(tag, None)
            print(Fore.GREEN +"[+] EXIF data removed successfully"+ Style.RESET_ALL)
        except:
            print(Fore.RED +"[-] EXIF data not found in the image"+ Style.RESET_ALL)

        #IPTC XMP
        try:
            iptc_info = IPTCInfo(img, verbosity=0)
            if iptc_info.iptc:
                iptc_info.data['keywords'] = []
                iptc_info.save_as(img)
            print(Fore.GREEN +"[+] IPTC and XMP data removed successfully"+ Style.RESET_ALL)
        except:
            print(Fore.RED +"[-] IPTC or XMP data not found in the image"+ Style.RESET_ALL)

        try:
            for pixel in data:
                if len(pixel) == 4:
                    clean_pixel = (pixel[0], pixel[1], pixel[2], 255)
                    clean_data.append(clean_pixel)
                else:
                    clean_data.append(pixel)
            print(Fore.GREEN +"[+] Metadata removed successfully"+ Style.RESET_ALL)
        except:
            print(Fore.RED +"[-] No metadata found in image"+ Style.RESET_ALL)


        cl_img = Image.new(image.mode, image.size)
        cl_img.putdata(clean_data)

        print(Fore.GREEN +"> Saving clean image..."+ Style.RESET_ALL)
        cl_img.save('clean-' + img)
    
    img = input("> Enter the image to remove metadata from: ")
    remove(img)


# Extract
def extract_metadata():
    def extract(img):
        metadata = {}
        
        #EXIF
        with Image.open(img) as img:
            try:
                raw_exif = img._getexif()
                for tag, value in raw_exif.items():
                    decoded_tag = TAGS.get(tag, tag)
                    metadata[decoded_tag] = value
            except AttributeError:
                print(Fore.RED +"[-] EXIF data not found in the image"+ Style.RESET_ALL)

        #IPTC
        try:
            info = IPTCInfo(img, force=True, verbosity=0)
            iptc_data = info.data
            for key, value in iptc_data.items():
                metadata[f'IPTC:{key}'] = value
        except:
            print(Fore.RED +"[-] IPTC data not found in the image"+ Style.RESET_ALL)

        #XMP
        try:
            img = pyexiv2.Image(img)
            img.read_metadata()
            xmp_data = img.xmp_data
            for key, value in xmp_data.items():
                metadata[f'XMP:{key}'] = value
        except:
            print(Fore.RED +"[-] XMP data not found in the image"+ Style.RESET_ALL)

        return metadata

    def generate_map(metadata):
        if 'GPSInfo' not in metadata:
            print(Fore.RED +"[-] GPS data not found in the image"+ Style.RESET_ALL)
            return
        
        try:
            gps_info = metadata['GPSInfo']
            lat = gps_info[2][0] + gps_info[2][1] / 60.0 + gps_info[2][2] / 3600.0
            lon = gps_info[4][0] + gps_info[4][1] / 60.0 + gps_info[4][2] / 3600.0
            
            m = folium.Map(location=[lat, lon], zoom_start=15)
            folium.Marker(location=[lat, lon]).add_to(m)

            m.save(f"{img}-map.html")
            print(Fore.GREEN +f"Map saved to '{img}-map.html'"+ Style.RESET_ALL)
        except:
            print(Fore.RED +"Could not extract GPS data"+ Style.RESET_ALL)


    img = input("> Enter the path of the image: ")
    metadata = extract(img)
    table = PrettyTable(["Metadata Tag", "Value"])
    for key, value in metadata.items():
        table.add_row([key, value])
    print(table)
    
    generate_map(metadata)
    
    save_csv = input("> Do you want to save the metadata to a CSV file? (1/0): ")
    if save_csv.lower() == '1':
        with open(f'{img}-log.csv', mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['Metadata Tag', 'Value'])
            for key, value in metadata.items():
                writer.writerow([key, value])
        print(Fore.GREEN +f"[+] Metadata saved to '{img}-log.csv'"+ Style.RESET_ALL)
    else:
        print(Fore.BLUE +"[-] Metadata was not saved to CSV file"+ Style.RESET_ALL)  
        
# Edit
def edit_metadata():
    def extract(img):
        try:
            exif_dict = piexif.load(img)
            with open(f"{img}-metadata.csv", "w", newline="") as f:
                writer = csv.writer(f)
                for ifd in ("0th", "Exif", "GPS", "1st"):
                    for tag in exif_dict[ifd]:
                        tag_name = piexif.TAGS[ifd][tag]["name"]
                        tag_value = exif_dict[ifd][tag]
                        writer.writerow([ifd, tag, tag_name, tag_value])
            print(Fore.GREEN +"[+] Metadata extracted successfully"+ Style.RESET_ALL)
        except:
            print(Fore.RED +"[-] Metadata not found in the image"+ Style.RESET_ALL)

    def load(img):
        try:
            exif_dict = piexif.load(img)
            with open(f"{img}-metadata.csv", "r", newline="") as f:
                reader = csv.reader(f)
                exif_dict = {"0th": {}, "Exif": {}, "GPS": {}, "1st": {}}
                for row in reader:
                    ifd = row[0]
                    tag = int(row[1])
                    tag_value = eval(row[3])
                    exif_dict[ifd][tag] = tag_value
            exif_bytes = piexif.dump(exif_dict)
            piexif.insert(exif_bytes, img)
            print(Fore.GREEN +"[+] Metadata loaded successfully"+ Style.RESET_ALL)
        except:
            print(Fore.RED +"[-] Metadata could not be loaded to the image"+ Style.RESET_ALL)

    print(Fore.BLUE +"1. Extract Metadata from image to editable format"+ Style.RESET_ALL)
    print(Fore.BLUE +"2. Load Metadata in image"+ Style.RESET_ALL)
    print(Fore.BLUE +"3. Exit"+ Style.RESET_ALL)

    choice = input("> Select operation: ")

    if choice == "1":
        img = input("> Enter image file to edit: ")
        extract(img)
    elif choice == "2":
        img = input("> Enter image file to edit: ")
        load(img)
    elif choice == "3":
        exit()
    else:
        print(Fore.RED +"Choice incorrect"+ Style.RESET_ALL)

        
#Choices
print(Fore.BLUE +"1. Remove Metadata from image"+ Style.RESET_ALL)
print(Fore.BLUE +"2. Extract Metadata from image"+ Style.RESET_ALL)
print(Fore.BLUE +"3. Edit metadata in image"+ Style.RESET_ALL)
print(Fore.BLUE +"4. Exit"+ Style.RESET_ALL)

choice = input("> Select operation: ")

if choice == "1":
    remove_metadata()
elif choice == "2":
    extract_metadata()
elif choice == "3":
    edit_metadata()
elif choice == "4":
    exit()
else:
    print(Fore.RED +"Choice incorrect"+ Style.RESET_ALL)
    
