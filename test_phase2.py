from core.plate_layout import PlateLayout, WellType
from analysis.validation_suite import ValidationSuite

# 1. Plate test
plate = PlateLayout("96")
plate.assign(0, WellType.TARGET, "GENE_A", 1000)
plate.assign(1, WellType.TARGET, "GENE_A", 100)
plate.assign(2, WellType.REFERENCE, "GAPDH", 1000)
plate.assign(3, WellType.NTC)
valid, msg = plate.validate()
print(f"Plate: {msg} | Aktif kuyu: {len(plate.get_active_wells())}")

# 2. Validation test
base = {'mg': 3.0, 'dntp': 0.2, 'ta': 60.0, 'tm': 58.0, 'cycles': 40, 
        'primer_uM': 250.0, 'polymerase_U': 1.0, 'dye': 'SYBR', 'copies': 1000, 'time_factor': 1.0}
suite = ValidationSuite(base)
dil = suite.run_dilution_series()
scan = suite.run_parameter_scan('mg', [1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5])
pdf_path = suite.generate_pdf_report(dil, scan)
print(f"Rapor oluşturuldu: {pdf_path}")
print(f"Slope: {dil['slope']:.3f} | R²: {dil['r2']:.3f} | E: {dil['efficiency']*100:.1f}%")