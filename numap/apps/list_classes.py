#!/usr/bin/env python
'''
List default classes supported in umap

Usage:
    numaplist [-v]

Options:
    -v, --verbose   show more information
'''
from numap.apps.base import NumapApp


class NumapListClassesApp(NumapApp):

    def run(self):
        ks = self.umap_classes
        verbose = self.options.get('--verbose', False)
        if verbose:
            print('%-20s  %s' % ('Device', 'Description'))
            print('--------------------  ----------------------------------------------------')
        for k in ks:
            if verbose:
                print('%-20s  %s' % (k, self.umap_class_dict[k][1]))
            else:
                print('%s' % k)


def main():
    app = NumapListClassesApp(__doc__)
    app.run()


if __name__ == '__main__':
    main()
