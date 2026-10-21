"""Layout-only repair of x-label/legend overlap; all frozen numeric source stays unchanged."""
import shutil
import plot_figures as figures
from reportlab.graphics.shapes import String,Line
original_save=figures.save

def final_save(drawing,name):
    for shape in drawing.contents:
      if isinstance(shape,String) and shape.text in ['Optimizer updates','Training seed']:shape.y=35
      if isinstance(shape,String) and shape.y==23:shape.y=11
      if isinstance(shape,Line) and shape.y1==shape.y2==26:shape.y1=shape.y2=14
    original_save(drawing,name)

def main():
    archive=figures.RUN/'figures-initial-layout';archive.mkdir(exist_ok=False)
    for p in (figures.RUN/'figures').iterdir():
      if p.is_file():shutil.copy2(p,archive/p.name)
    figures.save=final_save;figures.main()
    print('LAYOUT_ONLY_REPAIR; numerical sources and frozen recipe unchanged; original render retained')
if __name__=='__main__':main()
