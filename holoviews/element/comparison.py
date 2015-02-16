"""
Helper classes for comparing the equality of two holoview objects.

These classes are designed to integrate with unittest.TestCase (see
the tests directory) while making equality testing easily accessible
to the user.

For instance, to test if two Matrix objects are equal you can use:

Comparison.assertEqual(matrix1, matrix2)

This will raise an AssertionError if the two matrix objects are not
equal, including information regarding what exactly failed to match.

Note that this functionality could not be provided using comparison
methods on all objects as comparison opertors only return Booleans and
thus would not supply any information regarding *why* two elements are
considered different.
"""

from unittest.util import safe_repr
from unittest import TestCase
from numpy.testing import assert_array_almost_equal

from . import *
from ..core import Element, AdjointLayout, Overlay, Dimensioned, LayoutTree
from ..core.options import Options
from ..interface.pandas import *
from ..interface.seaborn import *


class ComparisonInterface(object):
    """
    This class is designed to allow equality testing to work
    seamlessly with unittest.TestCase as a mix-in by implementing a
    compatible interface (namely the assertEqual method).

    The assertEqual class method is to be overridden by an instance
    method of the same name when used as a mix-in with TestCase. The
    contents of the equality_type_funcs dictionary is suitable for use
    with TestCase.addTypeEqualityFunc.
    """

    equality_type_funcs = {}
    failureException = AssertionError

    @classmethod
    def simple_equality(cls, first, second, msg=None):
        """
        Classmethod equivalent to unittest.TestCase method (longMessage = False.)
        """
        if not first==second:
            standardMsg = '%s != %s' % (safe_repr(first), safe_repr(second))
            raise cls.failureException(msg or standardMsg)


    @classmethod
    def assertEqual(cls, first, second, msg=None):
        """
        Classmethod equivalent to unittest.TestCase method
        """
        asserter = None
        if type(first) is type(second):
            asserter = cls.equality_type_funcs.get(type(first))

            try:              basestring = basestring # Python 2
            except NameError: basestring = str        # Python 3

            if asserter is not None:
                if isinstance(asserter, basestring):
                    asserter = getattr(cls, asserter)

        if asserter is None:
            asserter = cls.simple_equality

        if msg is None:
            asserter(first, second)
        else:
            asserter(first, second, msg=msg)


class Comparison(ComparisonInterface):
    """
    Class used for comparing two holoview objects, including complex
    composite objects. Comparisons are available as classmethods, the
    most general being the assertEqual method that is intended to work
    with any input.

    For instance, to test if two Matrix objects are equal you can use:

    Comparison.assertEqual(matrix1, matrix2)
    """

    @classmethod
    def register(cls):

        # Float comparisons
        cls.equality_type_funcs[float] =        cls.compare_floats
        cls.equality_type_funcs[np.float] =     cls.compare_floats
        cls.equality_type_funcs[np.float32] =   cls.compare_floats
        cls.equality_type_funcs[np.float64] =   cls.compare_floats

        # Numpy array comparison
        cls.equality_type_funcs[np.ndarray] =   cls.compare_arrays

        # Dimension objects
        cls.equality_type_funcs[Dimension] =    cls.compare_dimensions
        cls.equality_type_funcs[Dimensioned] =  cls.compare_dimensioned  # Used in unit tests
        cls.equality_type_funcs[Element]     =  cls.compare_elements     # Used in unit tests

        # Composition (+ and *)
        cls.equality_type_funcs[Overlay] =       cls.compare_overlays
        cls.equality_type_funcs[LayoutTree] =    cls.compare_layouttrees

        # Annotations
        cls.equality_type_funcs[VLine] =       cls.compare_vline
        cls.equality_type_funcs[HLine] =       cls.compare_hline
        cls.equality_type_funcs[Spline] =      cls.compare_spline
        cls.equality_type_funcs[Arrow] =       cls.compare_arrow
        cls.equality_type_funcs[Text] =        cls.compare_text

        # Rasters
        cls.equality_type_funcs[Matrix] =       cls.compare_matrix

        # Charts
        cls.equality_type_funcs[Curve] =        cls.compare_curve
        cls.equality_type_funcs[Histogram] =    cls.compare_histogram
        cls.equality_type_funcs[Raster] =       cls.compare_raster
        cls.equality_type_funcs[HeatMap] =      cls.compare_heatmap

        # Tables
        cls.equality_type_funcs[ItemTable] =    cls.compare_itemtables
        cls.equality_type_funcs[Table] =        cls.compare_tables

        cls.equality_type_funcs[Contours] =     cls.compare_contours
        cls.equality_type_funcs[Points] =       cls.compare_points
        cls.equality_type_funcs[VectorField] =  cls.compare_vectorfield

        # Pandas DFrame objects
        cls.equality_type_funcs[DataFrameView] = cls.compare_dframe
        cls.equality_type_funcs[PandasDFrame] =  cls.compare_dframe
        cls.equality_type_funcs[DFrame] =        cls.compare_dframe

        # Seaborn Views
        cls.equality_type_funcs[Bivariate] =    cls.compare_bivariate
        cls.equality_type_funcs[Distribution] = cls.compare_distribution
        cls.equality_type_funcs[Regression] =   cls.compare_regression
        cls.equality_type_funcs[TimeSeries] =   cls.compare_timeseries

        # NdMappings
        cls.equality_type_funcs[NdLayout] =      cls.compare_gridlayout
        cls.equality_type_funcs[AdjointLayout] = cls.compare_adjointlayouts
        cls.equality_type_funcs[NdOverlay] =     cls.compare_ndoverlays
        cls.equality_type_funcs[AxisLayout] =    cls.compare_grids
        cls.equality_type_funcs[HoloMap] =       cls.compare_holomap

        # Option objects
        cls.equality_type_funcs[Options] =     cls.compare_options

        return cls.equality_type_funcs


    #=====================#
    # Literal comparisons #
    #=====================#

    @classmethod
    def compare_floats(cls, arr1, arr2, msg='Floats'):
        cls.compare_arrays(arr1, arr2, msg)

    @classmethod
    def compare_arrays(cls, arr1, arr2, msg='Arrays'):
        try:
            assert_array_almost_equal(arr1, arr2)
        except AssertionError as e:
            raise cls.failureException(msg + str(e)[11:])

    @classmethod
    def bounds_check(cls, el1, el2, msg=None):
        if el1.bounds.lbrt() != el2.bounds.lbrt():
            raise cls.failureException("BoundingBoxes are mismatched.")


    #=======================================#
    # Dimension and Dimensioned comparisons #
    #=======================================#


    @classmethod
    def compare_dimensions(cls, dim1, dim2, msg=None):
        if dim1.name != dim2.name:
            raise cls.failureException("Dimension names mismatched: %s != %s"
                                       % (dim1.name, dim2.name))
        if dim1.cyclic != dim2.cyclic:
            raise cls.failureException("Dimension cyclic declarations mismatched.")
        if dim1.range != dim2.range:
            raise cls.failureException("Dimension ranges mismatched: %s != %s"
                                       % (dim1.range, dim2.range))
        if dim1.type != dim2.type:
            raise cls.failureException("Dimension type declarations mismatched: %s != %s"
                                       % (dim1.type,dim2.type))
        if dim1.unit != dim2.unit:
            raise cls.failureException("Dimension unit declarations mismatched: %s != %s"
                                       % (dim1.unit , dim2.unit))
        if dim1.values != dim2.values:
            raise cls.failureException("Dimension value declarations mismatched: %s != %s"
                                       % (dim1.values , dim2.values))
        if dim1.format_string != dim2.format_string:
            raise cls.failureException("Dimension format string declarations mismatched: %s != %s"
                                       % (dim1.format_string , dim2.format_string))

    @classmethod
    def compare_labelled_data(cls, obj1, obj2, msg=None):
        cls.assertEqual(obj1.value, obj2.value, "Value labels mismatched.")
        cls.assertEqual(obj1.label, obj2.label, "Labels mismatched.")

    @classmethod
    def compare_dimension_lists(cls, dlist1, dlist2, msg='Dimension lists'):
        if len(dlist1) != len(dlist2):
            raise cls.failureException('%s mismatched' % msg)
        for d1, d2 in zip(dlist1, dlist2):
            cls.assertEqual(d1, d2)

    @classmethod
    def compare_dimensioned(cls, obj1, obj2, msg=None):
        cls.compare_labelled_data(obj1, obj2)
        cls.compare_dimension_lists(obj1.value_dimensions, obj2.value_dimensions,
                                    'Value dimension list')
        cls.compare_dimension_lists(obj1.key_dimensions, obj2.key_dimensions,
                                    'Key dimension list')

    @classmethod
    def compare_elements(cls, obj1, obj2, msg=None):
        cls.compare_labelled_data(obj1, obj2)
        cls.assertEqual(obj1.data, obj2.data)


    #===============================#
    # Compositional trees (+ and *) #
    #===============================#

    @classmethod
    def compare_trees(cls, el1, el2, msg='Trees'):
        if len(el1.keys()) != len(el2.keys()):
            raise cls.failureException("%s have mismatched path counts." % msg)
        if el1.keys() != el2.keys():
            raise cls.failureException("%s have mismatched paths." % msg)
        for element1, element2 in zip(el1.values(),  el2.values()):
            cls.assertEqual(element1, element2)

    @classmethod
    def compare_layouttrees(cls, el1, el2, msg=None):
        cls.compare_dimensioned(el1, el2)
        cls.compare_trees(el1, el2, msg='LayoutTrees')

    @classmethod
    def compare_overlays(cls, el1, el2, msg=None):
        cls.compare_dimensioned(el1, el2)
        cls.compare_trees(el1, el2, msg='Overlays')


    #================================#
    # AttrTree and Map based classes #
    #================================#

    @classmethod
    def compare_ndmappings(cls, el1, el2, msg='NdMappings'):
        cls.compare_dimensioned(el1, el2)
        if len(el1.keys()) != len(el2.keys()):
            raise cls.failureException("%s have different numbers of keys." % msg)

        if set(el1.keys()) != set(el2.keys()):
            raise cls.failureException("%s have different sets of keys." % msg)

        for element1, element2 in zip(el1, el2):
            cls.assertEqual(element1, element2)

    @classmethod
    def compare_holomap(cls, el1, el2, msg='HoloMaps'):
        cls.compare_dimensioned(el1, el2)
        cls.compare_ndmappings(el1, el2, msg)


    @classmethod
    def compare_gridlayout(cls, el1, el2, msg=None):
        cls.compare_dimensioned(el1, el2)

        if len(el1) != len(el2):
            raise cls.failureException("GridLayouts have different sizes.")

        if set(el1.keys()) != set(el2.keys()):
            raise cls.failureException("GridLayouts have different keys.")

        for element1, element2 in zip(el1, el2):
            cls.assertEqual(element1,element2)


    @classmethod
    def compare_ndoverlays(cls, el1, el2, msg=None):
        cls.compare_dimensioned(el1, el2)
        if len(el1) != len(el2):
            raise cls.failureException("NdOverlays have different lengths.")

        for (layer1, layer2) in zip(el1, el2):
            cls.assertEqual(layer1, layer2)

    @classmethod
    def compare_adjointlayouts(cls, el1, el2, msg=None):
        cls.compare_dimensioned(el1, el2)
        for element1, element2 in zip(el1, el1):
            cls.assertEqual(element1, element2)


    #=============#
    # Annotations #
    #=============#

    @classmethod
    def compare_annotation(cls, el1, el2, msg='Annotation'):
        cls.compare_dimensioned(el1, el2)
        cls.assertEqual(el1.data, el2.data)

    @classmethod
    def compare_hline(cls, el1, el2, msg='HLine'):
        cls.compare_annotation(el1, el2, msg=msg)

    @classmethod
    def compare_vline(cls, el1, el2, msg='VLine'):
        cls.compare_annotation(el1, el2, msg=msg)

    @classmethod
    def compare_spline(cls, el1, el2, msg='Spline'):
        cls.compare_annotation(el1, el2, msg=msg)

    @classmethod
    def compare_arrow(cls, el1, el2, msg='Arrow'):
        cls.compare_annotation(el1, el2, msg=msg)

    @classmethod
    def compare_text(cls, el1, el2, msg='Text'):
        cls.compare_annotation(el1, el2, msg=msg)


    #========#
    # Charts #
    #========#

    @classmethod
    def compare_curve(cls, el1, el2, msg=None):
        cls.compare_dimensioned(el1, el2)
        cls.compare_arrays(el1.data, el2.data, 'Curve data')


    @classmethod
    def compare_histogram(cls, el1, el2, msg=None):
        cls.compare_dimensioned(el1, el2)
        cls.compare_arrays(el1.edges, el2.edges, "Histogram edges")
        cls.compare_arrays(el1.values, el2.values, "Histogram values")


    @classmethod
    def compare_raster(cls, el1, el2, msg=None):
        cls.compare_dimensioned(el1, el2)
        cls.compare_arrays(el1.data, el2.data, 'Raster data')


    @classmethod
    def compare_heatmap(cls, el1, el2, msg=None):
        cls.compare_dimensioned(el1, el2)
        cls.compare_arrays(el1.data, el2.data, 'HeatMap data')

    @classmethod
    def compare_contours(cls, el1, el2, msg=None):
        cls.compare_dimensioned(el1, el2)
        if len(el1) != len(el2):
            raise cls.failureException("Contours do not have a matching number of contours.")

        for c1, c2 in zip(el1.data, el2.data):
            cls.compare_arrays(c1, c2, 'Contour data')

    @classmethod
    def compare_points(cls, el1, el2, msg=None):
        cls.compare_dimensioned(el1, el2)
        if len(el1) != len(el2):
            raise cls.failureException("Points objects have different numbers of points.")

        cls.compare_arrays(el1.data, el2.data, 'Points data')

    @classmethod
    def compare_vectorfield(cls, el1, el2, msg=None):
        cls.compare_dimensioned(el1, el2)
        if len(el1) != len(el2):
            raise cls.failureException("VectorField objects have different numbers of vectors.")

        cls.compare_arrays(el1.data, el2.data, 'VectorField data')


    #=========#
    # Rasters #
    #=========#

    @classmethod
    def compare_matrix(cls, el1, el2, msg='Matrix data'):
        cls.compare_dimensioned(el1, el2)
        cls.compare_arrays(el1.data, el2.data, msg=msg)
        cls.bounds_check(el1,el2)


    #========#
    # Tables #
    #========#

    @classmethod
    def compare_itemtables(cls, el1, el2, msg=None):
        cls.compare_dimensioned(el1, el2)
        if el1.rows != el2.rows:
            raise cls.failureException("ItemTables have different numbers of rows.")

        if el1.cols != el2.cols:
            raise cls.failureException("ItemTables have different numbers of columns.")

        if [d.name for d in el1.value_dimensions] != [d.name for d in el2.value_dimensions]:
            raise cls.failureException("ItemTables have different Dimensions.")


    @classmethod
    def compare_tables(cls, el1, el2, msg=None):
        cls.compare_dimensioned(el1, el2)
        if el1.rows != el2.rows:
            raise cls.failureException("Tables have different numbers of rows.")

        if el1.cols != el2.cols:
            raise cls.failureException("Tables have different numbers of columns.")

        cls.compare_ndmappings(el1, el2, msg)


    #========#
    # Pandas #
    #========#

    @classmethod
    def compare_dframe(cls, el1, el2, msg=None):
        cls.compare_dimensioned(el1, el2)
        from pandas.util.testing import assert_frame_equal
        try:
            assert_frame_equal(el1.data, el2.data)
        except AssertionError as e:
            raise cls.failureException(msg+': '+str(e))

    #=========#
    # Seaborn #
    #=========#

    @classmethod
    def compare_distribution(cls, el1, el2, msg=None):
        cls.compare_dimensioned(el1, el2)
        cls.compare_arrays(el1.data, el2.data, 'Distribution data')

    @classmethod
    def compare_timeseries(cls, el1, el2, msg=None):
        cls.compare_dimensioned(el1, el2)
        cls.compare_arrays(el1.data, el2.data, 'TimeSeries data')

    @classmethod
    def compare_bivariate(cls, el1, el2, msg=None):
        cls.compare_dimensioned(el1, el2)
        cls.compare_arrays(el1.data, el2.data, 'Bivariate data')

    @classmethod
    def compare_regression(cls, el1, el2, msg=None):
        cls.compare_dimensioned(el1, el2)
        cls.compare_arrays(el1.data, el2.data, 'Regression data')

    #=======#
    # Grids #
    #=======#

    @classmethod
    def _compare_grids(cls, el1, el2, name):

        if len(el1.keys()) != len(el2.keys()):
            raise cls.failureException("%ss have different numbers of items." % name)

        if set(el1.keys()) != set(el2.keys()):
            raise cls.failureException("%ss have different keys." % name)

        if len(el1) != len(el2):
            raise cls.failureException("%ss have different depths." % name)

        for element1, element2 in zip(el1, el2):
            cls.assertEqual(element1, element2)

    @classmethod
    def compare_grids(cls, el1, el2, msg=None):
        cls.compare_dimensioned(el1, el2)
        cls._compare_grids(el1, el2, 'AxisLayout')

    #=========#
    # Options #
    #=========#

    @classmethod
    def compare_options(cls, options1, options2, msg=None):
        cls.assertEqual(options1.kwargs, options2.kwargs)


    @classmethod
    def compare_channelopts(cls, opt1, opt2, msg=None):
        cls.assertEqual(opt1.mode, opt2.mode)
        cls.assertEqual(opt1.pattern, opt2.pattern)
        cls.assertEqual(opt1.patter, opt2.pattern)



class ComparisonTestCase(Comparison, TestCase):
    """
    Class to integrate the Comparison class with unittest.TestCase.
    """

    def __init__(self, *args, **kwargs):
        TestCase.__init__(self, *args, **kwargs)
        registry = Comparison.register()
        for k, v in registry.items():
            self.addTypeEqualityFunc(k, v)
